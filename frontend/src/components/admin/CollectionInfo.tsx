interface CollectionInfoProps {
  blogId: string;
  totalQueries: number;
}

export function CollectionInfo({ blogId, totalQueries }: CollectionInfoProps) {
  const collections = [
    { id: "blog-v2", label: "IT Blog" },
    { id: "investment", label: "Investment Blog" },
  ];

  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <p className="mb-3 text-sm font-medium">인덱싱 현황</p>
      <ul className="space-y-2">
        {collections.map((col) => (
          <li key={col.id} className="flex items-center justify-between text-sm">
            <span>{col.label}</span>
            <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
              {col.id}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-muted-foreground">
        총 질문 수: {totalQueries}건
      </p>
    </div>
  );
}
