function changeShifts() {
    const opportunity_dropdown = document.getElementById("volunteer_position")
    var my_name = opportunity_dropdown.value 
    // console.log(my_name)

    const shifts_info = document.querySelector("#shifts_info #shifts_" + my_name)
    var cloned = shifts_info.cloneNode(true)
    
    // Clear existing and add new
    const form_location = document.getElementById("shifts_submission")
    form_location.replaceChildren(cloned)
}

function secondaryShifts() {
    const opportunity_dropdown = document.getElementById("secondary_position")
    var my_name = opportunity_dropdown.value 
    // console.log(my_name)

    const shifts_info = document.querySelector("#shifts_info #shifts_" + my_name)
    var cloned = shifts_info.cloneNode(true)

    // change checkbox names
    inputs = cloned.querySelectorAll("input")
    for (var i = 0; i < inputs.length; i++) {
        //console.log(inputs[i])
        var my_box = inputs[i]
        my_box.name = "secondary_" + my_box.name
    }
    
    // Clear existing and add new
    const form_location = document.getElementById("secondary_submission")
    form_location.replaceChildren(cloned)
}

document.addEventListener('DOMContentLoaded', function () {
    const opportunity_dropdown = document.getElementById("volunteer_position") 
    const secondary_dropdown = document.getElementById("secondary_position")

    opportunity_dropdown.addEventListener('change', changeShifts)
    secondary_dropdown.addEventListener('change', secondaryShifts)
})