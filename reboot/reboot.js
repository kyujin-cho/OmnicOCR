const TelegramBot = require('node-telegram-bot-api')
const tmi = require('tmi.js')
const exec = require('child_process').exec
const options = require('./config')

var client = new tmi.client(options)

// Connect the client to the server..
client.connect()
client.on('connected', (address, port) => {
    client.join('#' + process.argv[2])    
})
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
    setTimeout(timer_func, 5000)
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

client.on("message", function (channel, userstate, message, self) {
    // Don't listen to my own messages..
    if (self) return;

    if(message.startsWith('!파업신고 ') && channel.substring(1) == process.argv[2]) {
        console.log(channel + '채널에서 파업신고! ')
        const child = exec('sudo service yousabot restart', restart_process)        
    }
})