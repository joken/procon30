import java.awt.*
import javax.swing.*
import javax.swing.border.LineBorder

val CELL_SIZE = 30

// GUIウィンドウ
class Window(val matchID: Long, private val ownTeamID: Long){

    private val gamePanel = JPanel()                        // ゲーム盤面のパネル
    private var pointPanels: List<List<PointPanel>>? = null // 各ポイントの書かれたパネル
    private val statusPanel = StatusPanel(ownTeamID)        // 各チームの情報の書かれたパネル
    private val frame: JFrame = JFrame("Procon30: $matchID")     // windowの側
    private val inputPanelsPanel = JPanel()
    private var inputPanels: List<InputPanel>? = null
    private val postButton = PostButton(matchID)

    init {
        frame.defaultCloseOperation = JFrame.EXIT_ON_CLOSE

        val panel = JPanel()
        panel.layout = BorderLayout()
        frame.add(panel)

        panel.add(statusPanel, BorderLayout.NORTH)

        panel.add(inputPanelsPanel, BorderLayout.EAST)

        gamePanel.preferredSize = Dimension(500, 500)
        panel.add(gamePanel, BorderLayout.CENTER)

        panel.add(postButton, BorderLayout.SOUTH)

        frame.isVisible = true
    }

    // 取得したデータでゲーム情報の更新を行う
    fun updateGame(match: Match){
        if (pointPanels == null) {
            gamePanel.preferredSize = Dimension(CELL_SIZE * match.width, CELL_SIZE * match.height)
            gamePanel.layout = GridLayout(match.height, match.width)
            pointPanels = match.points.map {
                it.map { it1 ->
                    PointPanel(it1)
                }
            }
            pointPanels?.forEach {
                it.forEach { it1 ->
                    gamePanel.add(it1)
                }
            }
            val agentCount = match.teams[0].agents.size
            inputPanelsPanel.layout = GridLayout(agentCount, 1)
            match.teams.forEach {
                if (it.teamID == ownTeamID) {
                    inputPanels = it.agents.map { agent ->
                        val ip = InputPanel(agent.agentID, ownTeamID, matchID, postButton)
                        inputPanelsPanel.add(ip)
                        ip
                    }
                }
                frame.pack()
            }
        }
        match.tiled.forEachIndexed { index1, list ->
            list.forEachIndexed { index2, e ->
                pointPanels!![index1][index2].background = getPanelColor(e)
            }
        }

        pointPanels!!.forEach {
            it.forEach { it1 ->
                it1.agentID = null
            }
        }

        val agent2Position = HashMap<Long, Agent>()

        match.teams.forEach {
            it.agents.forEach { agent ->
                pointPanels!![agent.y - 1][agent.x - 1].setAgent(agent, it.teamID == ownTeamID)
                agent2Position[agent.agentID] = agent
            }
        }

        match.actions.filter { it.turn == match.turn }.forEach {
            val actionedAgent = agent2Position[it.agentID]
            if (actionedAgent != null) {
                pointPanels!![actionedAgent.y - 1][actionedAgent.x - 1].action = it
            }
        }

        statusPanel.updateStatus(match.teams)
        inputPanels?.forEach {
            it.update(match)
        }
        gamePanel.repaint()

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
    var action: Action? = null

    init {
        this.layout = BorderLayout()
        this.border = LineBorder(Color.BLACK)
        val pointLabel = JLabel(point.toString()).also {
            it.verticalAlignment = JLabel.CENTER
            it.horizontalAlignment = JLabel.CENTER
            it.minimumSize = Dimension(CELL_SIZE, CELL_SIZE)
            it.preferredSize = Dimension(CELL_SIZE, CELL_SIZE)
//            it.isOpaque = false
//            it.border = LineBorder(Color.DARK_GRAY)
        }
        this.preferredSize = Dimension(CELL_SIZE, CELL_SIZE)
        this.minimumSize = Dimension(CELL_SIZE, CELL_SIZE)
        this.add(pointLabel)
    }

    fun setAgent(agent: Agent, isOwnTeam: Boolean){
        agentID = agent.agentID
        agentIsOwnTeam = isOwnTeam
    }

    override fun paintComponent(g: Graphics) {
        super.paintComponent(g)
        if (agentID != null){
            if (agentIsOwnTeam) {
                g.color = Color.WHITE
            }else{
                g.color = Color(200, 200, 200, 255)
            }
            g as Graphics2D
            g.stroke = BasicStroke(3.0f)
            g.drawOval(5, 5, CELL_SIZE-10, CELL_SIZE-10)
            g.color = Color.BLACK
            if (agentIsOwnTeam)
                g.drawString(agentID.toString(), 1, 10)
            if (action != null){
                when(action!!.type){
                    "move" -> {
                        when (action!!.apply) {
                            0 -> {
                                g.color = Color.BLUE
                            }
                            -1 -> {
                                g.color = Color.RED
                            }
                            1 -> {
                                g.color = Color.YELLOW
                            }
                        }
                        g.drawOval(CELL_SIZE/2+action!!.dx*10-5/2, CELL_SIZE/2+action!!.dy*10-5/2, 5, 5)
                    }
                    "remove" -> {
                        when (action!!.apply) {
                            0 -> {
                                g.color = Color.BLUE
                            }
                            -1 -> {
                                g.color = Color.RED
                            }
                            1 -> {
                                g.color = Color.ORANGE
                            }
                        }
                        g.drawOval(CELL_SIZE/2+action!!.dx*10-5/2, CELL_SIZE/2+action!!.dy*10-5/2, 5, 5)
                    }
                    "stay" -> {
                        when (action!!.apply) {
                            0 -> {
                                g.color = Color.BLUE
                            }
                            -1 -> {
                                g.color = Color.RED
                            }
                            1 -> {
                                g.color = Color.GREEN
                            }
                        }
                        g.drawOval(CELL_SIZE / 2 - 5 / 2, CELL_SIZE / 2 - 5 / 2, 5, 5)
                    }
                }
            }
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

class PostButton(private val matchID: Long): JButton("POST"){
    val actions = Actions(mutableListOf())

    init {
        this.addActionListener {
            postAction(matchID, actions)
            (actions.actions as MutableList).clear()
        }
    }
}
