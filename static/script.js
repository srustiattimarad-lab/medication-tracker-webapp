console.log("Medication Tracker Loaded");


/* =========================================
   MEDICATION REMINDER & NOTIFICATION SYSTEM
========================================= */


// Ask browser notification permission
document.addEventListener("DOMContentLoaded", function () {

    if ("Notification" in window) {

        Notification.requestPermission()
            .then(permission => {
                console.log("Notification Permission:", permission);
            });

    }

});


// Convert time to minutes
// Supports BOTH:
// 24-hour → 18:30
// 12-hour → 06:30 PM

function timeToMinutes(timeStr) {

    if (!timeStr) return 0;

    timeStr = timeStr.trim();

    // 24-hour format
    if (!timeStr.includes("AM") && !timeStr.includes("PM")) {

        let parts = timeStr.split(":");

        let hours = parseInt(parts[0]);
        let minutes = parseInt(parts[1]);

        return (hours * 60) + minutes;
    }

    // 12-hour format
    let [time, modifier] = timeStr.split(" ");

    let [hours, minutes] = time.split(":");

    hours = parseInt(hours);
    minutes = parseInt(minutes);

    if (modifier === "PM" && hours !== 12) {
        hours += 12;
    }

    if (modifier === "AM" && hours === 12) {
        hours = 0;
    }

    return (hours * 60) + minutes;
}


// Show notification
function showNotification(title, message) {

    if (Notification.permission === "granted") {

        new Notification(title, {
            body: message,
            icon: "https://cdn-icons-png.flaticon.com/512/2966/2966489.png"
        });

    }

}


// Prevent duplicate notifications
let notifiedMedicines = {};


// Check medicines every 30 seconds
setInterval(function () {

    let medicines = document.querySelectorAll(".medicine-card");

    let now = new Date();

    let currentMinutes =
        (now.getHours() * 60) + now.getMinutes();

    medicines.forEach(card => {

        let nameElement = card.querySelector(".med-name");
        let timeElement = card.querySelector(".med-time");
        let statusElement = card.querySelector(".status");

        if (!nameElement || !timeElement || !statusElement) {
            return;
        }

        let medicineName = nameElement.innerText.trim();

        let medicineTime = timeElement.innerText.trim();

        let medicineStatus = statusElement.innerText.trim();

        let medicineMinutes =
            timeToMinutes(medicineTime);

        // Unique key
        let reminderKey =
            medicineName + "-" + medicineTime;

        // Reminder Notification
        if (
            currentMinutes === medicineMinutes &&
            medicineStatus === "Pending" &&
            !notifiedMedicines[reminderKey]
        ) {

            showNotification(
                "💊 Medication Reminder",
                "Time to take " + medicineName
            );

            notifiedMedicines[reminderKey] = true;
        }

        // Missed Medicine Notification
        if (
            currentMinutes > medicineMinutes &&
            medicineStatus === "Pending" &&
            !notifiedMedicines[reminderKey + "-missed"]
        ) {

            showNotification(
                "⚠ Medicine Missed",
                medicineName + " was not taken on time."
            );

            notifiedMedicines[reminderKey + "-missed"] = true;
        }

    });

}, 30000);



