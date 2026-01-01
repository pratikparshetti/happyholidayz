document.addEventListener('DOMContentLoaded', () => {
    refreshFileList();
});

function generateItinerary() {
    const days = document.getElementById('days').value;
    const output = document.getElementById('itinerary-output');

    // Don't overwrite if content already exists to prevent accidental data loss, 
    // unless user explicitly wants to (simplified here: just append/create if empty or confirm)
    if (output.innerHTML.trim() !== "") {
        if (!confirm("This will overwrite the current itinerary view. Continue?")) return;
    }

    output.innerHTML = '';

    for (let i = 1; i <= days; i++) {
        const div = document.createElement('div');
        div.className = 'day-box';
        div.innerHTML = `
            <h3>Day ${i}</h3>
            <textarea id="day-${i}" placeholder="Enter activities for Day ${i}..."></textarea>
        `;
        output.appendChild(div);
    }
}

async function saveItinerary() {
    const destination = document.getElementById('destination').value;
    const startDate = document.getElementById('start-date').value;
    const days = document.getElementById('days').value;
    const filenameInput = document.getElementById('save-filename').value;

    // Gather day activities
    const dayActivities = {};
    for (let i = 1; i <= days; i++) {
        const el = document.getElementById(`day-${i}`);
        if (el) {
            dayActivities[`day_${i}`] = el.value;
        }
    }

    const data = {
        meta: {
            destination: destination,
            startDate: startDate,
            days: days
        },
        activities: dayActivities,
        filename: filenameInput
    };

    try {
        const response = await fetch('/api/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        showMessage(result.message, result.success);
        refreshFileList();
    } catch (error) {
        showMessage("Error saving file: " + error, false);
    }
}

async function refreshFileList() {
    try {
        const response = await fetch('/api/list');
        const result = await response.json();
        const select = document.getElementById('load-file-select');
        select.innerHTML = '<option value="">Select a saved trip...</option>';
        result.files.forEach(file => {
            const opt = document.createElement('option');
            opt.value = file;
            opt.textContent = file;
            select.appendChild(opt);
        });
    } catch (error) {
        console.error("Could not fetch file list", error);
    }
}

async function loadItinerary() {
    const filename = document.getElementById('load-file-select').value;
    if (!filename) return;

    try {
        const response = await fetch(`/api/load/${filename}`);
        const data = await response.json();

        // Populate fields
        document.getElementById('save-filename').value = data.filename || filename.replace('.json', ''); // attempt to restore user friendly name

        if (data.meta) {
            document.getElementById('destination').value = data.meta.destination || '';
            document.getElementById('start-date').value = data.meta.startDate || '';
            document.getElementById('days').value = data.meta.days || 3;
        }

        // Regenerate the boxes first
        const output = document.getElementById('itinerary-output');
        output.innerHTML = '';
        const numDays = data.meta ? data.meta.days : (Object.keys(data.activities).length || 3);

        for (let i = 1; i <= numDays; i++) {
            const div = document.createElement('div');
            div.className = 'day-box';

            const activityText = data.activities[`day_${i}`] || '';

            div.innerHTML = `
                <h3>Day ${i}</h3>
                <textarea id="day-${i}" placeholder="Enter activities for Day ${i}...">${activityText}</textarea>
            `;
            output.appendChild(div);
        }

        showMessage("Itinerary loaded successfully!", true);

    } catch (error) {
        showMessage("Error loading file: " + error, false);
    }
}

function showMessage(msg, success) {
    const el = document.getElementById('message-area');
    el.textContent = msg;
    el.style.color = success ? 'green' : 'red';
    setTimeout(() => { el.textContent = ''; }, 3000);
}
