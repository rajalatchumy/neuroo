var ip = "";

// Function to get the user's IP address using JavaScript
// Function to get the user's IP address using JavaScript
function getIPAddress(callback) {
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "https://api.ipify.org?format=json", true);
  xhr.onload = function () {
    if (xhr.status >= 200 && xhr.status < 300) {
      var responseData = JSON.parse(xhr.responseText);
      callback(responseData.ip);
    } else {
      console.error("Request failed. Status:", xhr.status);
      callback(null);
    }
  };
  xhr.onerror = function () {
    console.error("Request failed");
    callback(null);
  };
  xhr.send();
}

// Function to detect browser
function getBrowserInfo() {
  const ua = navigator.userAgent;
  if (/OPR|Opera/.test(ua)) return 'Opera';
  else if (/Edg/.test(ua)) return 'Edge';
  else if (/Chrome/.test(ua) && !/OPR|Edg/.test(ua)) return 'Chrome';
  else if (/Safari/.test(ua) && !/Chrome/.test(ua)) return 'Safari';
  else if (/Firefox/.test(ua)) return 'Firefox';
  else if (/MSIE|Trident/.test(ua)) return 'IE';
  else return 'Unknown';
}

// Function to get OS info
function getOSInfo() {
  const platform = navigator.platform;
  if (platform.toLowerCase().includes('win')) return 'Windows';
  else if (platform.toLowerCase().includes('mac')) return 'MacOS';
  else if (platform.toLowerCase().includes('linux')) return 'Linux';
  else return 'Unknown';
}

// Function to append messages to chat box
function appendMessage(message, message1) {
  const chatBox = $("#r");
  const newMessage = $('<div class="direct-chat-msg" style="color:blue"></div>').html(message).hide();
  const newMessage1 = $('<div class="direct-chat-msg" style="float:right;color:#1100ff;"></div>').html(message1).hide();
  chatBox.append(newMessage);
  chatBox.append(newMessage1);
  newMessage.fadeIn("slow");
  newMessage1.fadeIn("slow");
}

// Function to send message
async function sendMessage() {
  const currentDate = new Date();
  const formattedDateTime = currentDate.toISOString();

  const ipAddress = await getClientIP(); // Fetch IP address

  $.post({
    url: "search",
    data: {
      query: $("#status_message").val(),
      ip: ipAddress,
      browser: getBrowserInfo(),
      dt: formattedDateTime,
      tz: Intl.DateTimeFormat().resolvedOptions().timeZone
    },
    success: function (res) {
      appendMessage($("#status_message").val(), res);
      $("#status_message").val("");
    }
  });
}

// Function to get client IP address asynchronously
async function getClientIP() {
  try {
    const response = await fetch('https://ipinfo.io/json');
    if (!response.ok) throw new Error('IP address lookup failed');
    const data = await response.json();
    return data.ip;
  } catch (error) {
    console.error('Error fetching IP:', error);
    return 'Unknown';
  }
}

// Handling DOM ready state
$(function () {
  $("#addClass").click(function () {
    $("#qnimate").addClass("popup-box-on");
  });

  $("#removeClass").click(function () {
    $("#qnimate").removeClass("popup-box-on");
  });

  // Handle Enter key press
  $("#status_message").keypress(function (e) {
    if (e.which === 13) {
      e.preventDefault();
      checking();
    }
  });
});

// Checking function to limit messages
function checking() {
  if ($("#r").children().length < 15) {
    sendMessage();
  } else {
    appendMessage($("#status_message").val(), "For further discussion contact info@ymetry.com");
    $("#status_message").val("");
  }
}

$("#da").on("click", function () {
  checking();
});

// Create a new visit
async function createVisit() {
  const clientIP = await getClientIP();
  const postData = {
    enter_timestamp: Date.now(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    landing_page: window.location.href,
    browser: getBrowserInfo(),
    os: getOSInfo(),
    ip_address: clientIP
  };

  fetch('/new_visit', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(postData)
  })
  .then(response => {
    if (response.ok) {
      console.log('Visit created successfully');
    } else {
      console.error('Failed to create visit');
    }
  })
  .catch(error => {
    console.error('Error creating visit:', error);
  });
}

// Ensure a visit is created each time the page is loaded
$(document).ready(function() {
  createVisit();
});



element = document.getElementById("qnimate")
makeResizable(element,10,10)
function makeResizable(element, minW = 130, minH = 130, size = 20) {
    const left = document.createElement('div');
    left.style.width = size + 'px';
    left.style.height = '100%';
    left.style.backgroundColor = 'transparent';
    left.style.position = 'absolute';
    left.style.top = '0px';
    left.style.left = - (size/2) + 'px';
    left.style.cursor = 'e-resize';

    left.addEventListener('mousedown', resizeXNegative());

    element.appendChild(left);

    const top = document.createElement('div');
    top.style.width = '100%';
    top.style.height = size + 'px';
    top.style.backgroundColor = 'transparent';
    top.style.position = 'absolute';
    top.style.top = - (size/2) + 'px';
    top.style.left = '0px';
    top.style.cursor = 'n-resize';

    top.addEventListener('mousedown', resizeYNegative());

    element.appendChild(top);

    const corner1 = document.createElement('div');
    corner1.style.width = size + 'px';
    corner1.style.height = size + 'px';
    corner1.style.backgroundColor = 'transparent';
    corner1.style.position = 'absolute';
    corner1.style.top = - (size/2) + 'px';
    corner1.style.left = - (size/2) + 'px';
    corner1.style.cursor = 'nw-resize';

    corner1.addEventListener('mousedown', resizeXNegative());
    corner1.addEventListener('mousedown', resizeYNegative());

    element.appendChild(corner1);

    function get_int_style(key) {
        return parseInt(window.getComputedStyle(element).getPropertyValue(key));
    }

    function resizeXNegative() {
        let startX;
        let startW;
        function dragMouseDown(e) {
            if(e.button !== 0) return;
            e = e || window.event;
            e.preventDefault();
            const {clientX} = e;
            startX = get_int_style('left');
            startW = get_int_style('width');

            document.addEventListener('mousemove', elementDrag);
            document.addEventListener('mouseup', closeDragElement);
        }

        function elementDrag(e) {
            const {clientX} = e;
            let w = startW + startX - clientX;
            if(w < minW) w = minW;
            if(w < 400) w = 400; // Restricting minimum width to 300px

            // Check if resizing beyond right boundary of viewport
            const maxRight = window.innerWidth;
            if (startX + startW - w > maxRight) {
                w = startX + startW - maxRight;
            }

            element.style.width = w + 'px';
        }

        function closeDragElement() {
            document.removeEventListener("mousemove", elementDrag);
            document.removeEventListener("mouseup", closeDragElement);
        }
        return dragMouseDown;
    }

    function resizeYNegative() {
        let startY;
        let startH;
        function dragMouseDown(e) {
            if(e.button !== 0) return;
            e = e || window.event;
            e.preventDefault();
            const {clientY} = e;
            startY = get_int_style('top');
            startH = get_int_style('height');

            document.addEventListener('mousemove', elementDrag);
            document.addEventListener('mouseup', closeDragElement);
        }

        function elementDrag(e) {
    const { clientY } = e;
    let h = startH + startY - clientY;

    // Set the minimum height constraint (adjust as needed)
    const minH = 400; // Minimum height (in pixels)
    if (h < minH) {
        h = minH;
    }

    // Set the maximum height constraint (adjust as needed)
    const maxH = 700; // Maximum height (in pixels)
    if (h > maxH) {
        h = maxH;
    }

    // Check if resizing beyond the bottom boundary of the viewport
    const maxBottom = window.innerHeight;
    if (startY + startH - h > maxBottom) {
        h = startY + startH - maxBottom;
    }

    // Apply the new height to the element
    element.style.height = h + 'px';
}


        function closeDragElement() {
            document.removeEventListener("mousemove", elementDrag);
            document.removeEventListener("mouseup", closeDragElement);
        }
        return dragMouseDown;
    }
}