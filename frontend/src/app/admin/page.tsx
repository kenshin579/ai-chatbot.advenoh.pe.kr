import { CollectionInfo } from "@/components/admin/CollectionInfo";
import { QueryChart } from "@/components/admin/QueryChart";
import { StatsCard } from "@/components/admin/StatsCard";
import { TopQuestions } from "@/components/admin/TopQuestions";
import { getAdminStats } from "@/lib/api";

export default async function AdminPage() {
  let stats;
  try {
    stats = await getAdminStats();
  } catch {
    return (
      <div className="p-8 text-sm text-destructive">
        통계 데이터를 불러오지 못했습니다.
      </div>
    );
  }

  const totalQueries = stats.daily_queries.reduce((s, d) => s + d.count, 0);

  return (
    <div className="bg-background p-8">
      <h1 className="mb-6 text-2xl font-bold">Admin 대시보드</h1>

      {/* 통계 카드 */}
      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatsCard
          title="총 질문 수"
          value={totalQueries}
          description="전체 누적"
        />
        <StatsCard
          title="피드백 점수"
          value={`${Math.round(stats.feedback_score.up_ratio * 100)}%`}
          description={`👍 ${stats.feedback_score.up} / 👎 ${stats.feedback_score.down}`}
        />
        <StatsCard
          title="평균 응답 시간"
          value={`${(stats.avg_response_time / 1000).toFixed(1)}s`}
          description="retrieval + generation"
        />
        <StatsCard
          title="검색 실패율"
          value={`${Math.round(stats.search_failure_rate * 100)}%`}
          description="관련 문서 미발견"
        />
      </div>

      {/* 일별 차트 */}
      <div className="mb-6">
        <QueryChart data={stats.daily_queries} />
      </div>

      {/* 인기 질문 + 인덱싱 현황 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <TopQuestions data={stats.top_questions} />
        <CollectionInfo blogId="blog-v2" totalQueries={totalQueries} />
      </div>
    </div>
  );
}
