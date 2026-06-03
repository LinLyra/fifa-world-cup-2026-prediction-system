type Props = {
  columns: string[];
  rows: Record<string, string | number>[];
};

export default function DataTable({ columns, rows }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-[#E0E8E3] bg-white">
      <table className="dashboard-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col}>{row[col]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
