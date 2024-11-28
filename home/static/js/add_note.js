// Function to get CSRF token from cookies
function getCSRFTokenFromCookie() {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.startsWith('csrftoken=')) {
            return cookie.substring('csrftoken='.length);
        }
    }
    return null; // Return null if CSRF token is not found
}

document.addEventListener('DOMContentLoaded', () => {
    // Add event listeners to all "Add Note" buttons
    document.querySelectorAll('.add-note-btn').forEach(button => {
        button.addEventListener('click', event => {
            event.preventDefault();

            const objectId = button.dataset.objectId;       // e.g., 1, 2, 3
            const objectType = button.dataset.objectType;   // e.g., 'pension', 'category'
            const noteCell = document.getElementById(`note-cell-${objectType}-${objectId}`);

            // Replace the button with a form for note input
            noteCell.innerHTML = `
                <form id="add-note-form-${objectType}-${objectId}" class="flex">
                    <input type="text" name="note" placeholder="Enter note" class="input input-bordered w-full" required />
                    <button type="submit" class="btn btn-success ml-2">Save</button>
                </form>
            `;

            // Add event listener to the dynamically created form
            document.getElementById(`add-note-form-${objectType}-${objectId}`).addEventListener('submit', function (e) {
                e.preventDefault();

                const formData = new FormData(this);
                formData.append('object_id', objectId);
                formData.append('object_type', objectType);
                formData.append('csrfmiddlewaretoken', getCSRFTokenFromCookie()); // Get CSRF token from cookies

                fetch(addNoteUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCSRFTokenFromCookie(), // Use CSRF token from cookies
                    },
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        noteCell.innerHTML = data.note; // Update the DOM with the new note
                    } else {
                        alert('Failed to add note. ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while adding the note.');
                });
            });
        });
    });
});
