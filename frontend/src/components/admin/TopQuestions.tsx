interface TopQuestionsProps {
  data: { question: string; count: number }[];
}

export function TopQuestions({ data }: TopQuestionsProps) {
  return (
    <div className="rounded-lg border bg-card p-4 shadow-sm">
      <p className="mb-3 text-sm font-medium">인기 질문 TOP 10</p>
      {data.length === 0 ? (
        <p className="text-sm text-muted-foreground">데이터 없음</p>
      ) : (
        <ol className="space-y-2">
          {data.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="min-w-[20px] font-medium text-muted-foreground">
                {i + 1}.
              </span>
              <span className="flex-1 truncate">{item.question}</span>
              <span className="text-muted-foreground">{item.count}회</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
