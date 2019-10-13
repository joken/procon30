import java.awt.*
import javax.swing.JFrame
import javax.swing.JLabel
import javax.swing.JLayeredPane
import javax.swing.JPanel
import javax.swing.border.LineBorder

// GUIウィンドウ
class Window(matchID: Long, private val ownTeamID: Long){

    private val gamePanel = JPanel()                        // ゲーム盤面のパネル
    private var pointPanels: List<List<PointPanel>>? = null // 各ポイントの書かれたパネル
    private val statusPanel = StatusPanel(ownTeamID)        // 各チームの情報の書かれたパネル
    private val frame: JFrame = JFrame("Procon30: $matchID")     // windowの側

    init {
        frame.defaultCloseOperation = JFrame.EXIT_ON_CLOSE

        val panel = JPanel()
        panel.layout = BorderLayout()
        frame.add(panel)

        panel.add(statusPanel, BorderLayout.NORTH)

        gamePanel.preferredSize = Dimension(500, 500)
        panel.add(gamePanel, BorderLayout.CENTER)


        frame.isVisible = true
    }

    // 取得したデータでゲーム情報の更新を行う
    fun updateGame(match: Match){
        if (pointPanels == null){
            gamePanel.layout = GridLayout(match.height, match.width)
            pointPanels = match.points.map {
                it.map { it1 ->
                    PointPanel(it1)
                }
            }
            pointPanels?.forEach {
                it.forEach{ it1 ->
                    gamePanel.add(it1)
                }
            }
        }
        match.tiled.forEachIndexed { index1, list ->
            list.forEachIndexed { index2, e ->
                pointPanels!![index1][index2].background = getPanelColor(e)
            }
        }

        pointPanels!!.forEach {
            it.forEach{ it1 ->
                it1.agentID = null
            }
        }

        match.teams.forEach{
            it.agents.forEach { agent ->
                pointPanels!![agent.y-1][agent.x-1].setAgent(agent, it.teamID == ownTeamID)
            }
        }

        statusPanel.updateStatus(match.teams)
        frame.pack()
    }

    private fun getPanelColor(tiled: Int): Color{
        return when(tiled){
            0 -> Color.WHITE                    // 空白
            ownTeamID.toInt() -> Color.CYAN     // 自分
            else -> Color.RED                   // 相手
        }
    }
}

class PointPanel(point: Int): JPanel(){

    var agentID: Long? = null
    var agentIsOwnTeam = false

    init {
        this.border = LineBorder(Color.BLACK)
        val layeredPane = JLayeredPane()
        this.add(layeredPane)
        val pointLabel = JLabel(point.toString())
        this.add(pointLabel)
    }

    fun setAgent(agent: Agent, isOwnTeam: Boolean){
        agentID = agent.agentID
        agentIsOwnTeam = isOwnTeam
    }

    override fun paintComponent(g: Graphics) {
        super.paintComponent(g)
        if (agentID != null){
            val g2 = g as Graphics2D
            g.drawString(agentID.toString(), 10, 12)
            if (agentIsOwnTeam) {
                g.color = Color(50, 50, 200, 70)
            }else{
                g.color = Color(200, 50, 50, 70)
            }
            g.stroke = BasicStroke(3.0f)
            g.drawOval(10, 10, 20, 20)
        }
    }
}

class StatusPanel(private val ownTeamID: Long): JPanel() {
    private val ownTeamLabel = JLabel()
    private val anotherTeamLabel = JLabel()

    init {
        this.layout = GridLayout(1, 2)

        ownTeamLabel.horizontalAlignment = JLabel.CENTER
        anotherTeamLabel.horizontalAlignment = JLabel.CENTER
        ownTeamLabel.isOpaque = true
        anotherTeamLabel.isOpaque = true
        ownTeamLabel.border = LineBorder(Color.BLACK)
        anotherTeamLabel.border = LineBorder(Color.BLACK)
        this.add(ownTeamLabel)
        this.add(anotherTeamLabel)
    }

    fun updateStatus(teams: List<Team>){
        teams.forEach {
            if (it.teamID == ownTeamID){
                ownTeamLabel.text = buildLabelString(it)
                ownTeamLabel.background = getTeamColor(it)
            }else{
                anotherTeamLabel.text = buildLabelString(it)
                anotherTeamLabel.background = getTeamColor(it)
            }
        }
    }

    private fun buildLabelString(team: Team) = """
        <html>
        teamID: ${team.teamID}<br>
        tilePoint: ${team.tilePoint}<br>
        areaPoint: ${team.areaPoint}<br>
        Point: ${team.tilePoint+team.areaPoint}
        </html>
        """.trimIndent()

    private fun getTeamColor(team: Team): Color{
        return when(team.teamID){
            0L -> Color.WHITE           // 空白
            ownTeamID -> Color.CYAN     // 自分
            else -> Color.RED           // 相手
        }
    }
}