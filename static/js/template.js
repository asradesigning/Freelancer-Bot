

// Tooltip Logic
function handleTooltip(triggerId, tooltipBoxId) {
    const tooltipTrigger = document.getElementById(triggerId);
    const tooltipBox = document.getElementById(tooltipBoxId);

    tooltipTrigger.addEventListener('mouseenter', () => {
        const rect = tooltipTrigger.getBoundingClientRect();
        tooltipBox.style.top = `${rect.bottom + window.scrollY + 10}px`;
        tooltipBox.style.left = `${rect.left}px`;
        tooltipBox.style.display = 'block';
    });

    tooltipTrigger.addEventListener('mouseleave', () => {
        tooltipBox.style.display = 'none';
    });
}

// Apply to all tooltips
handleTooltip('customizeTooltipTrigger', 'customizeTooltipBox');
handleTooltip('skillTooltipTrigger', 'skillTooltipBox');
handleTooltip('priceTooltipTrigger', 'priceTooltipBox');


  document.querySelectorAll('.on-btn, .off-btn').forEach(button => {
    button.addEventListener('click', function () {
        const parent = button.parentElement;
        const onButton = parent.querySelector('.on-btn');
        const offButton = parent.querySelector('.off-btn');

        // Add active class to the clicked button, remove from the other
        if (button.classList.contains('on-btn')) {
            onButton.classList.add('active');
            offButton.classList.remove('active');
            if(button.name == "Client"){
                document.getElementById("client").value = "ON";
            }
            else if(button.name == "User"){
                document.getElementById("user").value = "ON";
            }
            else if(button.name == "Sealed"){
                document.getElementById("sealed").value = "ON";
            }
        } else {
            offButton.classList.add('active');
            onButton.classList.remove('active');
            if(button.name == "Client"){
                document.getElementById("client").value = "OFF";
            }
            else if(button.name == "User"){
                document.getElementById("user").value = "OFF";
            }
            else if(button.name == "Sealed"){
                document.getElementById("sealed").value = "OFF";
            }
        }
    });
});

// Toggle functionality and form submission
document.querySelectorAll('.toggle-container').forEach(toggle => {
    toggle.addEventListener('click', function () {
        this.classList.toggle('toggle-active');
        const toggleSwitch = this.querySelector('.toggle-switch');
        const input = this.closest('.toggle-item').querySelector('.skill_status'); // Find the .skill_status input in the parent

        // Toggle the text content of the toggle switch
        toggleSwitch.textContent = toggleSwitch.textContent === 'OFF' ? 'ON' : 'OFF';
        
        // Toggle the value of the hidden input field
        input.value = input.value === 'OFF' ? 'ON' : 'OFF';

        // Submit the form
        const form = this.closest('.toggle-item').querySelector('.skill_status_form');
        form.submit();
    });
});

// Handle button selection
document.querySelectorAll('.pricing-btn').forEach(button => {
    button.addEventListener('click', function () {
        const group = this.closest('form'); // Get the closest parent form
        const buttons = group.querySelectorAll('.pricing-btn');
        
        // Remove "selected" class from all buttons in the group
        buttons.forEach(btn => btn.classList.remove('selected'));
        
        // Add "selected" class to the clicked button
        this.classList.add('selected');

        // Update the hidden input value
        const fixedPriceInput = group.querySelector("#fixed-price");
        const hourlyPriceInput = group.querySelector("#hourly-price");
        const selectedValue = this.dataset.state;

        if (fixedPriceInput) {
            fixedPriceInput.value = selectedValue;
        } else if (hourlyPriceInput) {
            hourlyPriceInput.value = selectedValue;
        }

        // Submit the form
        group.submit();
    });
});


addLinkInput = document.getElementById('add-link-input');
addLinkButton = document.getElementById('add-link');
linkBox = document.getElementById('link-box');
linksInput = document.getElementById('all-links');

addLinkButton.addEventListener('click', function () {
    const linkValue = addLinkInput.value;

    // Exit if the input is empty
    if (addLinkInput.value == "") return;

    if (linkBox.children.length === 10) {
        alert("Only 10 links can be added");
        return;
    }    

    // Add the new link to the linkBox
    const tag = document.createElement('div');
    tag.classList.add("link");
    tag.classList.add("text-truncate");
    tag.innerText = linkValue;
    console.log(tag)
    linkBox.appendChild(tag);
    linksInput.value += linkValue + ", ";


    // Clear the input field
    addLinkInput.value = '';
})

bidBtn = document.querySelector('.start-bid-btn');
bidStatus = document.getElementById('bidding_status');
bidBtn.addEventListener('click', function(){
    console.log(bidStatus.value);
    if(bidStatus.value == "stopped"){
        bidBtn.innerText = "Start Bid Now";
        bidStatus.value = "bidding";
        console.log("Start Bidding");
    }
    else if(bidStatus.value == "bidding"){
        bidBtn.innerText = "Stop Bidding";
        bidStatus.value = "stopped";
        console.log("Stop Bidding");
    }
    this.parentElement.submit();
})

function updateCharCount() {
    const textarea = document.getElementById("intro");
    const charCount = document.getElementById("charCount");
    charCount.textContent = textarea.value.length + " / 250";
}