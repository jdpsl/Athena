import SwiftUI
import SwiftData

struct ContentView: View {
    @StateObject private var viewModel = ContentViewModel()
    @Environment(\.modelContext) private var modelContext
    @Query private var items: [Item]

    var body: some View {
        NavigationStack {
            VStack(spacing: 20) {
                // Header
                Text("Welcome to {{project_name}}")
                    .font(.largeTitle)
                    .fontWeight(.bold)

                // Counter Example
                HStack {
                    Button {
                        viewModel.decrementCounter()
                    } label: {
                        Image(systemName: "minus.circle.fill")
                            .font(.title)
                    }

                    Text("\(viewModel.counter)")
                        .font(.system(size: 48, weight: .bold))
                        .frame(minWidth: 100)

                    Button {
                        viewModel.incrementCounter()
                    } label: {
                        Image(systemName: "plus.circle.fill")
                            .font(.title)
                    }
                }
                .padding()
                .background(.ultraThinMaterial)
                .cornerRadius(16)

                // Items List
                if !items.isEmpty {
                    List {
                        ForEach(items) { item in
                            HStack {
                                Text(item.name)
                                Spacer()
                                Text(item.timestamp, style: .time)
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                        .onDelete(perform: deleteItems)
                    }
                    .frame(height: 200)
                } else {
                    Text("No items yet")
                        .foregroundStyle(.secondary)
                        .padding()
                }

                // Add Item Button
                Button {
                    addItem()
                } label: {
                    Label("Add Item", systemImage: "plus")
                        .frame(maxWidth: .infinity)
                }
                .buttonStyle(.borderedProminent)
                .padding(.horizontal)
            }
            .navigationTitle("{{project_name}}")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    EditButton()
                }
            }
        }
    }

    private func addItem() {
        let newItem = Item(name: "Item \(items.count + 1)")
        modelContext.insert(newItem)
        try? modelContext.save()
    }

    private func deleteItems(offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(items[index])
        }
        try? modelContext.save()
    }
}

#Preview {
    ContentView()
        .modelContainer(for: Item.self, inMemory: true)
}
