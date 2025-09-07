"use strict";

jQuery(document).ready(function ($) {
	var adpPopup = {};

	(function () {
		var $this;

		adpPopup = {
			sPrevious: window.scrollY,
			sDirection: "down",

			/*
			 * Initialize
			 */
			init: function (e) {
				$this = adpPopup;

				$this.popupInit(e);

				// Init events.
				$this.events(e);
			},

			/*
			 * Events
			 */
			events: function (e) {
				// Custom Events
				$(document).on("click", ".popup-close", $this.closePopup);
				$(document).on("click", ".popup-accept", $this.acceptPopup);
				$(document).on("click", ".popup-accept", $this.closePopup);
				$(document).on(
					"click",
					".age-verification__popup-close",
					$this.agePopup
				);
				$(document).on(
					"click",
					".age-verification__popup-close",
					$this.closePopup
				);
				$(document).on(
					"click",
					".age-verification__button-no",
					$this.ageDeclined
				);

				// Checking this will cause popup to close when user presses key.
				$(document).keyup(function (e) {
					// Press ESC to Close.
					if (e.key === "Escape") {
						$('.popup-open[data-esc-close="true"]').each(function (
							index,
							popup
						) {
							$this.closePopup(popup);
						});
					}

					// Press F4 to Close.
					if (e.key === "F4") {
						$('.popup-open[data-f4-close="true"]').each(function (
							index,
							popup
						) {
							$this.closePopup(popup);
						});
					}
				});

				// Checking this will cause popup to close when user clicks on overlay.
				$(document).on("click", ".popup-overlay", function (e) {
					$('.popup-open[data-overlay-close="true"]').each(function (
						index,
						popup
					) {
						$this.closePopup(popup);
						//$this.closePopup( $( this).prev() );
					});
				});
			},

			/*
			 * Init popup elements
			 */
			popupInit: function (e) {
				// Set scroll direction.
				$(document).on("scroll", function () {
					let scrollCurrent = window.scrollY;

					// Set scroll temporary vars.
					if (scrollCurrent > $this.sPrevious) {
						$this.sDirection = "down";
					} else {
						$this.sDirection = "up";
					}

					$this.sPrevious = scrollCurrent;
				});

				// Open popup
				$(".popup").each(function (index, popup) {
					// Manual Launch.
					if ("manual" === $(popup).data("open-trigger")) {
						let selector = $(popup).data("open-manual-selector");

						if (selector) {
							$(selector).addClass("popup-trigger");

							$(document).on("click", selector, function (e) {
								e.preventDefault();

								$(popup).removeClass("popup-already-opened");

								$this.openPopup(popup);

								if (e.currentTarget.classList.contains("popup")) {
									$this.closePopup(selector);
								}
							});
						}
					}

					// Checks whether a popup should be displayed or not.
					if (
						!$this.isAllowPopup(popup) &&
						!$(popup).hasClass("age-verification")
					) {
						return;
					}

					$this.openTriggerPopup(popup);
				});
			},

			/*
			 * Trigger open popup
			 */
			openTriggerPopup: function (e) {
				let popup = e.originalEvent ? this : e;

				var trigger = $(popup).data("open-trigger");

				// Age Verification.
				if ("none" === trigger) {
					let ageVerification = $this.getCookie(
						"popup-age-" + $(popup).data("id") || 0
					);

					if (!ageVerification) $this.openPopup(popup);
				}

				// Time Delay.
				if ("delay" === trigger) {
					setTimeout(function () {
						$this.openPopup(popup);
					}, $(popup).data("open-delay-number") * 1000);
				}

				// Exit Intent.
				if ("exit" === trigger) {
					var showExit = true;
					document.addEventListener("mousemove", function (e) {
						// Get current scroll position
						var scroll =
							window.pageYOffset || document.documentElement.scrollTop;
						if (e.pageY - scroll < 7 && showExit) {
							$this.openPopup(popup);
							showExit = false;
						}
					});
				}

				// Scroll Position.
				if ("scroll" === trigger) {
					var pointScrollType = $(popup).data("open-scroll-type");
					var pointScrollPosition = $(popup).data("open-scroll-position");

					// Event scroll.
					$(document).on("scroll", function () {
						// Type px.
						if ("px" === pointScrollType) {
							if (window.scrollY >= pointScrollPosition) {
								$this.openPopup(popup);
							}
						}

						// Type %.
						if ("%" === pointScrollType) {
							if ($this.getScrollPercent() >= pointScrollPosition) {
								$this.openPopup(popup);
							}
						}
					});
				}

				// Accept Agreement.
				if ("accept" === trigger) {
					let accept = $this.getCookie(
						"popup-accept-" + $(popup).data("id") || 0
					);

					if (!accept) {
						$this.openPopup(popup);
					}
				}
			},

			/*
			 * Trigger close popup
			 */
			closeTriggerPopup: function (e) {
				let popup = e.originalEvent ? this : e;

				var trigger = $(popup).data("close-trigger");

				// Time Delay.
				if ("delay" === trigger) {
					setTimeout(function () {
						$this.closePopup(popup);
					}, $(popup).data("close-delay-number") * 1000);
				}

				// Scroll Position.
				if ("scroll" === trigger) {
					var pointScrollType = $(popup).data("close-scroll-type");
					var pointScrollPosition = $(popup).data("close-scroll-position");
					var initScrollPx = $(popup).data("init-scroll-px");
					var initScrollPercent = $(popup).data("init-scroll-percent");

					// Event scroll.
					$(document).on("scroll", function () {
						// Type px.
						if ("px" === pointScrollType) {
							if (
								"up" === $this.sDirection &&
								window.scrollY < initScrollPx - pointScrollPosition
							) {
								$this.closePopup(popup);
							}

							if (
								"down" === $this.sDirection &&
								window.scrollY >= initScrollPx + pointScrollPosition
							) {
								$this.closePopup(popup);
							}
						}

						// Type %.
						if ("%" === pointScrollType) {
							if (
								"up" === $this.sDirection &&
								$this.getScrollPercent() <
									initScrollPercent - pointScrollPosition
							) {
								$this.closePopup(popup);
							}

							if (
								"down" === $this.sDirection &&
								$this.getScrollPercent() >=
									initScrollPercent + pointScrollPosition
							) {
								$this.closePopup(popup);
							}
						}
					});
				}
			},

			/*
			 * Open popup
			 */
			openPopup: function (e) {
				let popup = e.originalEvent ? this : e;

				// Hide body scroll.
				if ($(popup).is('[data-body-scroll-disable="true"]')) {
					$("body").addClass("popup-scroll-hidden");
				}

				// Set Cookie of Limit display.
				let limit =
					parseInt($this.getCookie("popup-" + $(popup).data("id")) || 0) + 1;

				$this.setCookie("popup-" + $(popup).data("id"), limit, {
					expires: $(popup).data("limit-lifetime"),
				});

				if ($(popup).hasClass("popup-open")) {
					return;
				}

				// Check already opened.
				if ($(popup).hasClass("popup-already-opened")) {
					return;
				}

				// Display popup.
				$(popup).addClass("popup-open");

				// Set current scroll.
				$(popup).data("init-scroll-px", window.scrollY);
				$(popup).data("init-scroll-percent", $this.getScrollPercent());

				// Open animation.
				let animation = $(popup).data("open-animation");

				$this.applyAnimation(popup, animation);

				// Init close trigger.
				$this.closeTriggerPopup(popup);
			},

			/*
			 * Age popup
			 */
			agePopup: function (e) {
				let $el = e.originalEvent ? this : e;

				// Get popup container.
				let popup = $($el).closest(".popup");

				// Set Cookie of Age.
				$this.setCookie("popup-age-" + $(popup).data("id"), 1, {
					expires: 360,
				});
			},

			/*
			 * Age declined
			 */

			ageDeclined: function () {
				$(".age-verification__question").removeClass("show");
				$(".age-verification__declined").addClass("show");
			},

			/*
			 * Accept popup
			 */
			acceptPopup: function (e) {
				let $el = e.originalEvent ? this : e;

				// Get popup container.
				let popup = $($el).closest(".popup");

				// Set Cookie of Accept.
				$this.setCookie("popup-accept-" + $(popup).data("id"), 1, {
					expires: 360,
				});
			},

			/*
			 * Close popup
			 */
			closePopup: function (e) {
				let $el = e.originalEvent ? this : e;

				// Get popup container.
				let popup = $($el).closest(".popup");

				// Close animation.
				let animation = $(popup).data("exit-animation");

				$this.applyAnimation(popup, animation, function () {
					// Already opened.
					$(popup).addClass("popup-already-opened");

					// Hide popup.
					$(popup).removeClass("popup-open");

					// Remove classes from body.
					$("body").removeClass("popup-scroll-hidden");
				});
			},

			/*
			 * Checks whether a popup should be displayed or not
			 */
			isAllowPopup: function (e) {
				let popup = e.originalEvent ? this : e;

				// Has user seen this popup before?
				let limitDisplay = parseInt($(popup).data("limit-display") || 0);

				let limitDisplayCookie = parseInt(
					$this.getCookie("popup-" + $(popup).data("id"))
				);

				if (
					limitDisplay &&
					limitDisplayCookie &&
					limitDisplayCookie >= limitDisplay
				) {
					return;
				}

				return true;
			},

			/*
			 * Apply animation
			 */
			applyAnimation: function (el, name, callback) {
				var popup = $(el).closest(".popup");

				if (typeof callback === "function") {
					var overlayName = "popupExitFade";
				} else {
					var overlayName = "popupOpenFade";
				}

				// Overlay Animation.
				$(popup)
					.next(".popup-overlay")
					.addClass("popup-animated " + overlayName)
					.one(
						"webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend",
						function () {
							$(this).removeClass("popup-animated " + overlayName);
						}
					);

				// Wrap Animation.
				$(popup)
					.find(".popup-wrap")
					.addClass("popup-animated " + name)
					.one(
						"webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend",
						function () {
							// remove the animation classes after animation ends
							// required in order to apply new animation on close
							$(this).removeClass("popup-animated " + name);

							if (typeof callback === "function") {
								callback();
							}
						}
					);
			},

			/*
			 * Set cookie
			 */
			getCookie: function (name) {
				var matches = document.cookie.match(
					new RegExp(
						"(?:^|; )" +
							name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, "\\$1") +
							"=([^;]*)"
					)
				);
				return matches ? decodeURIComponent(matches[1]) : undefined;
			},

			/*
			 * Set cookie
			 */
			setCookie: function (name, value, options) {
				options = options || {};

				options.path = options.hasOwnProperty("path") ? options.path : "/";

				options.expires = parseInt(options.expires);

				if (typeof options.expires == "number" && options.expires) {
					options.expires = new Date().setDate(
						new Date().getDate() + options.expires
					);

					options.expires = new Date(options.expires).toUTCString();
				}

				value = encodeURIComponent(value);

				var updatedCookie = name + "=" + value;

				for (var propName in options) {
					updatedCookie += "; " + propName;
					var propValue = options[propName];
					if (propValue !== true) {
						updatedCookie += "=" + propValue;
					}
				}

				document.cookie = updatedCookie;
			},

			/*
			 * Get scroll percent
			 */
			getScrollPercent: function () {
				var h = document.documentElement,
					b = document.body,
					st = "scrollTop",
					sh = "scrollHeight";
				return ((h[st] || b[st]) / ((h[sh] || b[sh]) - h.clientHeight)) * 100;
			},
		};
	})();

	// Initialize.
	adpPopup.init();

	document.addEventListener("shopify:section:load", function () {
		adpPopup.init();
	});

	document.addEventListener("shopify:section:unload", function () {
		$("body").removeClass("popup-scroll-hidden");
	});
});
