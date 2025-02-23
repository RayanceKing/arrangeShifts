import SwiftUI
import UniformTypeIdentifiers
import CoreXLSX // 需要安装该库处理 Excel

// MARK: - 数据模型
struct Staff: Identifiable, Hashable {
    let id = UUID()
    let name: String
    var availableDays: [Weekday]
}

enum Weekday: String, CaseIterable {
    case monday = "周一"
    case tuesday = "周二"
    case wednesday = "周三"
    case thursday = "周四"
    case friday = "周五"
}

struct ScheduleResult: Identifiable {
    let id = UUID()
    let weekday: Weekday
    var staff: [Staff]
}

// MARK: - 主视图
struct ContentView: View {
    @StateObject private var vm = ScheduleViewModel()
    
    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                // 文件选择区域
                filePickerSection
                
                // 排班结果展示
                resultList
                
                // 操作按钮
                actionButtons
            }
            .padding()
            .navigationTitle("智能排班系统")
            .background(
                LinearGradient(
                    colors: [Color(.systemTeal), .white],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
            )
            .alert("错误", isPresented: $vm.showError) {
                Button("确定", role: .cancel) { }
            } message: {
                Text(vm.errorMessage)
            }
            .sheet(item: $vm.selectedFile) { file in
                ScheduleDetailView(results: vm.scheduleResults)
            }
        }
    }
    
    // MARK: 子视图组件
    private var filePickerSection: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("选择排班数据文件")
                .font(.headline)
                .foregroundStyle(.secondary)
            
            HStack {
                Text(vm.selectedFile?.fileName ?? "未选择任何文件")
                    .lineLimit(1)
                    .padding(.vertical, 10)
                    .padding(.horizontal)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(.ultraThinMaterial)
                    .cornerRadius(8)
                
                Button {
                    vm.showFileImporter.toggle()
                } label: {
                    Label("浏览", systemImage: "folder")
                }
                .buttonStyle(.borderedProminent)
            }
        }
    }
    
    private var resultList: some View {
        Group {
            if vm.isLoading {
                ProgressView()
                    .scaleEffect(1.5)
            } else if !vm.scheduleResults.isEmpty {
                List {
                    ForEach(vm.scheduleResults) { result in
                        Section {
                            ForEach(result.staff) { staff in
                                Text(staff.name)
                            }
                        } header: {
                            HStack {
                                Text(result.weekday.rawValue)
                                Spacer()
                                Text("\(result.staff.count)人")
                            }
                        }
                    }
                }
                .scrollContentBackground(.hidden)
            } else {
                ContentUnavailableView(
                    "暂无排班数据",
                    systemImage: "calendar.badge.exclamationmark",
                    description: Text("请先选择 Excel 文件并生成排班")
                )
            }
        }
        .frame(maxHeight: .infinity)
    }
    
    private var actionButtons: some View {
        HStack(spacing: 20) {
            Button(role: .destructive) {
                vm.reset()
            } label: {
                Label("重置", systemImage: "trash")
            }
            .disabled(vm.selectedFile == nil)
            
            Button {
                vm.generateSchedule()
            } label: {
                Label("生成排班", systemImage: "gear")
            }
            .disabled(vm.selectedFile == nil)
            
            Button {
                vm.exportSchedule()
            } label: {
                Label("导出结果", systemImage: "square.and.arrow.up")
            }
            .disabled(vm.scheduleResults.isEmpty)
        }
        .buttonStyle(.borderedProminent)
    }
}

// MARK: - 视图模型
class ScheduleViewModel: ObservableObject {
    @Published var selectedFile: ScheduleFile?
    @Published var scheduleResults: [ScheduleResult] = []
    @Published var isLoading = false
    @Published var showError = false
    @Published var errorMessage = ""
    
    var showFileImporter = false
    
    // 文件导入逻辑
    func importFile(_ result: Result<URL, Error>) {
        do {
            let url = try result.get()
            guard url.startAccessingSecurityScopedResource() else {
                throw ScheduleError.fileAccessDenied
            }
            
            defer { url.stopAccessingSecurityScopedResource() }
            
            let data = try Data(contentsOf: url)
            selectedFile = ScheduleFile(data: data, fileName: url.lastPathComponent)
            
        } catch {
            handleError(error)
        }
    }
    
    // 排班生成逻辑
    func generateSchedule() {
        guard let file = selectedFile else { return }
        
        isLoading = true
        DispatchQueue.global(qos: .userInitiated).async {
            do {
                let staffList = try self.parseExcel(file.data)
                let schedule = try self.calculateSchedule(staffList)
                
                DispatchQueue.main.async {
                    self.scheduleResults = schedule
                    self.isLoading = false
                }
                
            } catch {
                self.handleError(error)
            }
        }
    }
    
    // Excel 解析
    private func parseExcel(_ data: Data) throws -> [Staff] {
        guard let file = try? XLSXFile(data: data) else {
            throw ScheduleError.invalidFileFormat
        }
        
        var staffList = [Staff]()
        
        for ws in try file.parseWorksheetPaths() {
            let worksheet = try file.parseWorksheet(at: ws)
            guard let sharedStrings = try file.parseSharedStrings() else { continue }
            
            for row in worksheet.data?.rows ?? [] {
                guard row.cells.count >= 2 else { continue }
                
                let nameCell = row.cells[0]
                let daysCell = row.cells[1]
                
                guard let name = nameCell.stringValue(sharedStrings) else { continue }
                guard let daysString = daysCell.stringValue(sharedStrings) else { continue }
                
                let days = daysString.components(separatedBy: ",")
                    .compactMap { Weekday(rawValue: $0.trimmingCharacters(in: .whitespaces)) }
                
                staffList.append(Staff(name: name, availableDays: days))
            }
        }
        
        guard !staffList.isEmpty else {
            throw ScheduleError.emptyData
        }
        
        return staffList
    }
    
    // 排班算法（保留原有逻辑）
    private func calculateSchedule(_ staffList: [Staff]) throws -> [ScheduleResult] {
        var availableDays: [Weekday: [Staff]] = [:]
        var shiftsCount: [Staff: Int] = [:]
        var schedule: [Weekday: [Staff]] = [:]
        
        // 初始化数据结构
        for weekday in Weekday.allCases {
            schedule[weekday] = []
        }
        
        for staff in staffList {
            shiftsCount[staff] = 0
            for day in staff.availableDays {
                availableDays[day, default: []].append(staff)
            }
        }
        
        // 按可用人数排序
        let sortedDays = Weekday.allCases.sorted {
            (availableDays[$0]?.count ?? 0) < (availableDays[$1]?.count ?? 0)
        }
        
        // 排班逻辑
        for day in sortedDays {
            guard var candidates = availableDays[day] else { continue }
            
            guard candidates.count >= 3 else {
                throw ScheduleError.insufficientStaff(day: day.rawValue)
            }
            
            let required = min(4, candidates.count)
            candidates.shuffle()
            let sortedCandidates = candidates.sorted { shiftsCount[$0]! < shiftsCount[$1]! }
            let selected = Array(sortedCandidates.prefix(required))
            
            for staff in selected {
                shiftsCount[staff]! += 1
            }
            
            schedule[day] = selected
        }
        
        return schedule.map { ScheduleResult(weekday: $0.key, staff: $0.value) }
            .sorted { $0.weekday.rawValue < $1.weekday.rawValue }
    }
    
    // 错误处理
    private func handleError(_ error: Error) {
        DispatchQueue.main.async {
            if let scheduleError = error as? ScheduleError {
                self.errorMessage = scheduleError.localizedDescription
            } else {
                self.errorMessage = error.localizedDescription
            }
            self.showError = true
            self.isLoading = false
        }
    }
    
    // 导出功能
    func exportSchedule() {
        // 实现导出逻辑（JSON/CSV/PDF等）
    }
    
    func reset() {
        selectedFile = nil
        scheduleResults.removeAll()
    }
}

// MARK: - 辅助类型
struct ScheduleFile: Identifiable {
    let id = UUID()
    let data: Data
    let fileName: String
}

enum ScheduleError: LocalizedError {
    case invalidFileFormat
    case emptyData
    case fileAccessDenied
    case insufficientStaff(day: String)
    
    var errorDescription: String? {
        switch self {
        case .invalidFileFormat:
            return "文件格式不支持，请选择.xlsx格式文件"
        case .emptyData:
            return "文件中未找到有效数据"
        case .fileAccessDenied:
            return "无法访问文件，请检查权限设置"
        case .insufficientStaff(let day):
            return "\(day) 可用人数不足3人"
        }
    }
}

// MARK: - 预览
#Preview {
    ContentView()
}