const TelegramBot = require('node-telegram-bot-api')
const tmi = require('tmi.js')
const exec = require('child_process').exec
const options = require('./config')
const token = 'MYTOKEN'
const bot = new TelegramBot(token, {polling: true})


var client = new tmi.client(options)

// Connect the client to the server..
client.connect()
client.join('#' + process.argv[2])

let build = ''

const restart_process = (error, stdout, stderr) => {
    console.log(`stdout: ${stdout}`);
    console.log(`stderr: ${stderr}`);
    if (error !== null) {
        console.log(`exec error: ${error}`);
    }
    build = process.argv[2] + ' 서버 재부팅 결과:\n'
    build += '표준 출력: ' + stdout + '\n'
    build += '에러: ' + stderr + '\n'      
    client.say('#' + process.argv[2], "서버가 재부팅되었습니다. 잠시 기다려주세요.")  
    setTimer(timer_func, 5000)
}

const timer_func = () => {
    exec('sudo service yousabot status | grep -A 1 Loaded: ',
        (error, stdout, stderr) => {
            console.log(`stdout: ${stdout}`);
            console.log(`stderr: ${stderr}`);
            if (error !== null) {
                console.log(`exec error: ${error}`);
            }          
            build += '상태: ' + stdout
            bot.sendMessage(msg.chat.id, build)                                         
        }
    )
}

bot.onText('/message/', (msg) => {
    const text = msg.text.split(' ')
    const streamer_name = text[0]
    if(streamer_name == process.argv[2]) {
        const child = exec('sudo service yousabot restart', restart_process)
    }
})
