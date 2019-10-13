data class PreMatch(
    val id: Long,
    val intervalMillis: Long,
    val matchTo: String,
    val teamID: Long,
    val turnMillis: Long,
    val turns: Long
)

data class Match(
    val startedAtUnixTime: Long,
    val points: List<List<Int>>,
    val tiled: List<List<Int>>,
    val teams: List<Team>,
    val turn: Int,
    val actions: List<Action>,
    val height: Int,
    val width: Int
)

data class Team(
    val agents: List<Agent>,
    val areaPoint: Long,
    val teamID: Long,
    val tilePoint: Long
)

data class Agent(
    val agentID: Long,
    val x: Int,
    val y: Int
)

data class Action(
    val agentID: Long,
    val apply: Int,
    val dx: Int,
    val dy: Int,
    val turn: Int,
    val type: String
)

data class TooEarly(
    val status: String,
    val startAtUnixTime: Long
)