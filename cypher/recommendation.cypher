// Mattress Type Recommendation (Collaborative filtering บน Graph)
// Parameters: $user, $limit
// me -PREFERS-> ที่นอนที่ชอบ <-PREFERS- ผู้ใช้อื่น -PREFERS-> ที่นอนอื่นที่ me ยังไม่เลือก
MATCH (me:User {name:$user})-[:PREFERS]->(shared:MattressType)
      <-[:PREFERS]-(other:User)-[:PREFERS]->(m:MattressType)
WHERE other <> me AND NOT EXISTS { MATCH (me)-[:PREFERS]->(m) }
RETURN m.name AS recommendation,
       count(*) AS score,                         // จำนวนเส้นทางที่ไปถึง
       collect(DISTINCT other.name) AS recommended_by,
       collect(DISTINCT shared.name) AS because_of
ORDER BY score DESC, recommendation
LIMIT $limit;
