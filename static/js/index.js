setInterval(update, 1000)

function update() {
    seconds = parseInt(document.getElementById("second_count").textContent) - 1
    minutes = parseInt(document.getElementById("minute_count").textContent)
    hours = parseInt(document.getElementById("hour_count").textContent)
    days = parseInt(document.getElementById("day_count").textContent)

    if (seconds < 0) {
        minutes -= 1
        seconds = 59
    }

    if (minutes < 0) {
        hours -= 1
        minutes = 59
    }

    if (hours < 0) {
        days -= 1
        hours = 23
    }
    
    document.getElementById("second_count").textContent = seconds
    document.getElementById("minute_count").textContent = minutes
    document.getElementById("hour_count").textContent = hours
    document.getElementById("day_count").textContent = days
}