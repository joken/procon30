import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.awt.BorderLayout
import java.awt.Color
import java.awt.GridLayout
import javax.swing.JButton
import javax.swing.JFrame
import javax.swing.JLabel
import javax.swing.JPanel
import javax.swing.border.LineBorder



class InputPanel(private val agentID: Long, private val teamID: Long, id: Long, private var postButton: PostButton? = null): JPanel(){

    private val inputButtonList = listOf(
        listOf(JButton("1"), JButton("2"), JButton("3")),
        listOf(JButton("4"), JButton("5"), JButton("6")),
        listOf(JButton("7"), JButton("8"), JButton("9"))
    )

    init {
        this.border = LineBorder(Color.BLACK, 1)
        val agentLabel = JLabel(agentID.toString()).also {
            it.verticalAlignment = JLabel.CENTER
            it.horizontalAlignment = JLabel.CENTER
            it.border = LineBorder(Color.BLACK, 2)
            it.isOpaque = true
            it.background = Color.CYAN
        }
        this.layout = GridLayout(3, 3)
        inputButtonList.forEachIndexed { index1, list ->
            list.forEachIndexed { index2, jButton ->
                if(index1 == 1 && index2 == 1){
                    this.add(agentLabel)
                }else {
                    jButton.addActionListener {
                        val doAction = DoAction(agentID, index2-1, index1-1, chooseMoveOrRemove(index1, index2))
                        println(postButton?.actions?.actions)

                        if (postButton != null) {
                            (postButton?.actions?.actions as MutableList).add(doAction)
                            return@addActionListener
                        }

                        val actions = Actions(listOf(doAction))
                        postAction(id, actions)
                    }
//                    jButton.isBorderPainted = false
                    val p = JPanel()
                    p.layout = BorderLayout()
                    p.add(jButton, BorderLayout.CENTER)
                    this.add(p)
                }
            }
        }
    }

    fun update(match: Match){
        match.teams.forEach {
            if (it.teamID == teamID){
                it.agents.forEach { agent ->
                    if (agent.agentID == agentID){
                        val x = agent.x-1
                        val y = agent.y-1
                        for(i in -1..1){
                            for(j in -1..1){
                                if(0<=i+x && i+x<match.width && 0<=j+y && j+y<match.height){
                                    inputButtonList[j+1][i+1].text = match.points[j+y][i+x].toString()
                                    inputButtonList[j+1][i+1].foreground = getPanelColor(match.tiled[j+y][i+x])
                                }else{
                                    inputButtonList[j+1][i+1].text = ""
                                    inputButtonList[j+1][i+1].foreground = Color.WHITE
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private fun getPanelColor(tiled: Int): Color{
        return when(tiled){
            0 -> Color.BLACK                    // 空白
            teamID.toInt() -> Color.BLUE     // 自分
            else -> Color.RED                   // 相手
        }
    }

    private fun chooseMoveOrRemove(index1: Int, index2: Int): String{
        return if (inputButtonList[index1][index2].foreground == Color.RED){
            "remove"
        }else{
            "move"
        }
    }
}

fun postAction(id: Long, actions: Actions){
    val json = jacksonObjectMapper().writeValueAsString(actions)
    val url = "http://$DOMAIN/matches/$id/action"
    val mediaTypeJson = "application/json".toMediaTypeOrNull()
    val requestBody = json.toRequestBody(mediaTypeJson)
    val request = Request.Builder().url(url).header("Authorization", TOKEN).post(requestBody).build()
    val client = OkHttpClient.Builder().build()
    val response = client.newCall(request).execute()
    println(response.body?.string())
}
