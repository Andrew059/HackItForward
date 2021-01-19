var url = document.location.href;

$(document).ready(() => {
  new Clipboard('.clipboard-btn', {
    text: function() {
      return url
    }
  });
	// Show / Hide menu when clicked
	$('.has-sub').on('click', function(e) {
		$('.dropdown-menu').not($(this).children('.dropdown-menu')).removeClass('dropdown-shown'); // Hide other menus
		$('.has-sub').not($(this)).removeClass('active');
		$(this).children('.dropdown-menu').toggleClass('dropdown-shown');
		$(this).toggleClass('active');
	});

	// TOGGLE HEADER-NAV
	$('#header-btn').on('click', function(e) {
		$('#header-menu').toggleClass('active');
		$('.nav-btn').toggleClass('active');
	});

	// Remove parent upon clicking close button
	$('.btn-close').on('click', function() {
		$(this).closest('div').remove();
	});
});

$(document).scroll(function() {
  checkOffset();
});

function checkOffset() {
  if($('#social-float').offset().top + $('#social-float').height()
                                         >= $('#footer').offset().top - 10)
      $('#social-float').css('position', 'absolute');
  if($(document).scrollTop() + window.innerHeight < $('#footer').offset().top)
      $('#social-float').css('position', 'fixed'); // restore when you scroll up
}

function openTab(evt, level) {
  var i, tabcontent, tablevel;

  // Get all elements with class="tabcontent" and hide them
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }

  // Get all elements with class="tablevel" and remove the class "selected"
  tablevel = document.getElementsByClassName("tablevel");
  for (i = 0; i < tablevel.length; i++) {
    tablevel[i].classList.remove("selected");
  }

  // Show the current tab, and add an "selected" class to the button that opened the tab
  document.getElementById(level).style.display = "block";
  evt.currentTarget.classList.add("selected");
}

function displayLinkCopied(id=0) {
  if (id != 0) {
    var popup = document.getElementById("copy-popup-1");
    popup.classList.toggle("show");

    setTimeout(function() {
      $('#copy-popup-1').fadeOut('fast');
  }, 2000);
  } else {
    var popup = document.getElementById("copy-popup");
    popup.classList.toggle("show");
    setTimeout(function() {
      $('#copy-popup').fadeOut('fast');
  }, 2000);

  }
}

function shareOnFB(url){
  var link = "https://www.facebook.com/sharer/sharer.php?u=" + url;
  window.open(link);
}

function shareOnTwitter(url){
  var link = "https://twitter.com/intent/tweet?url=" + url + "&text=" + document.querySelector('#initiative-name').textContent;
  TwitterWindow = window.open(link);
}

function shareOnLinkedIn(url){
  var link = "https://www.linkedin.com/sharing/share-offsite/?url=" + url;
  window.open(link);
}

function shareOnReddit(url) {
  var link = "https://reddit.com/submit?url="+ url + "&title=" + document.querySelector('#initiative-name').textContent;
  window.open(link);
}

function getRandomUnsplash() {

}
