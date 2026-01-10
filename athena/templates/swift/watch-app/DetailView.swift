import SwiftUI

struct DetailView: View {
    let item: WatchItem

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 12) {
                Text(item.title)
                    .font(.headline)

                Text(item.description)
                    .font(.body)
                    .foregroundStyle(.secondary)

                Text("Created: \(item.timestamp, style: .time)")
                    .font(.caption)
                    .foregroundStyle(.tertiary)
            }
            .padding()
        }
        .navigationTitle("Details")
    }
}

#Preview {
    NavigationStack {
        DetailView(item: WatchItem(
            title: "Sample Item",
            description: "This is a sample description"
        ))
    }
}
