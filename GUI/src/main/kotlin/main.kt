import com.fasterxml.jackson.module.kotlin.jacksonObjectMapper
import com.fasterxml.jackson.module.kotlin.readValue
import okhttp3.OkHttpClient
import okhttp3.Request
import java.util.*
import java.util.TimerTask as TimerTask

var TOKEN = "localhost:8000"
var DOMAIN = "procon30_example_token"

// TOKEN DOMAIN
fun main(args: Array<String>) {
    val token = args[0]
    val domain = args[1]

    println("token = $token")
    println("domain = $domain")

    TOKEN = token
    DOMAIN = domain

    val preMatchList = getPreMatch()
    if(preMatchList == null){
        println("cannot get preMatch")
        return
    }
    println(preMatchList)

    preMatchList.forEach {
        startViewer(it)
    }

}

fun startViewer(preMatch: PreMatch){
    val id = preMatch.id
    val turnMillis = preMatch.turnMillis
    val intervalMillis = preMatch.intervalMillis
    val startAtUnixTime = getMatchBeforeStart(id)
    println(startAtUnixTime)
    println(System.currentTimeMillis()/1000L)
    val window = Window(preMatch.id, preMatch.teamID)
    while (System.currentTimeMillis()/1000L < startAtUnixTime){
        Thread.sleep(1000)
    }

    val timer = Timer()
    fun gameUpdateLoop(){
        val match = getMatch(id)
        println(match)
        if (match == null){
            println("cannot get match")
            return
        }
        window.updateGame(match)
    }
    val task = object : TimerTask(){
        override fun run() {
            gameUpdateLoop()
        }
    }
    timer.scheduleAtFixedRate(task, 0L, turnMillis+intervalMillis)
}

fun getPreMatch(): List<PreMatch>? {
    val responce = get("http://$DOMAIN/matches/")
    return jacksonObjectMapper().readValue(responce ?: return null)
}

fun getMatch(id: Long): Match? {
    val url = "http://$DOMAIN/matches/$id"
    val responce = get(url)
    return jacksonObjectMapper().readValue<Match>(responce ?: return null)
}

fun getMatchBeforeStart(id: Long): Long {
    val request = Request.Builder().url("http://$DOMAIN/matches/$id").header("Authorization", TOKEN).build()
    val client = OkHttpClient.Builder().build()
    val response = client.newCall(request).execute()
    println(response.code)
    println(response.body.toString())
    if (response.code == 400 && response.body.toString().contains("TooEarly")){
        return jacksonObjectMapper().readValue<TooEarly>(response.body.toString()).startAtUnixTime
    }
    return 0L
}

fun get(url: String): String? {
    val request = Request.Builder().url(url).header("Authorization", TOKEN).build()
    val client = OkHttpClient.Builder().build()
    val response = client.newCall(request).execute()
    return response.body?.string()
}
