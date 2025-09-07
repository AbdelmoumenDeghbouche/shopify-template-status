class PromoPopup extends HTMLElement {
  constructor() {
    super();

    // Prevent popup on Shopify robot challenge page
    if (window.location.pathname === '/challenge') {
      return;
    }

    this.cookieName = 'lumin:promo-popup';

    this.classes = {
      bodyClass: 'promo-popup--open',
      activeClass: 'is-active',
      closingClass: 'is-closing',
      showImage: 'show-image'
    };

    this.popup = this.querySelector('.promo-popup');

    // Open modal if errors or success message exist
    if (this.querySelector('.form__message')) {
      this.open();
    }

    

    this.querySelectorAll('.popup-close, .popup-overlay').forEach((button) => {
      button.addEventListener('click', this.close.bind(this));
    });

    this.querySelectorAll('.popup-open').forEach((button) => {
      button.addEventListener('click', this.open.bind(this));
    });

    if (!this.getCookie(this.cookieName) || this.dataset.testMode === 'true') {
      this.init();
    }

    if (Shopify.designMode) {
      document.addEventListener('shopify:section:load', (event) => filterShopifyEvent(event, this, () => this.open.bind(this)));
      document.addEventListener('shopify:section:select', (event) => filterShopifyEvent(event, this, this.open.bind(this)));
      document.addEventListener('shopify:section:deselect', (event) => filterShopifyEvent(event, this, this.close.bind(this)));
    }
  }

  init() {
    if (Shopify && Shopify.designMode) {
      return;
    }

    setTimeout(function() {
      this.open();
    }.bind(this), parseInt(this.dataset.delay) * 1000);
  }

  open() {
    document.body.classList.remove(this.classes.bodyClass);
    this.popup.classList.add(this.classes.activeClass);
    setTimeout(() => {
      this.popup.classList.add(this.classes.showImage);
    }, 600);

    if (this.dataset.position === 'center') {
      setScrollbarWidth();
      document.body.classList.add(this.classes.bodyClass);
    }
  }

  close() {
    this.popup.classList.add(this.classes.closingClass);

    setTimeout(() => {
      this.popup.classList.remove(this.classes.activeClass);
      this.popup.classList.remove(this.classes.closingClass);
      this.popup.classList.remove(this.classes.showImage);

      if (this.dataset.position === 'center') {
        document.body.classList.remove(this.classes.bodyClass);
      }
    }, 500);

    // Remove a cookie in case it was set in test mode
    if (this.dataset.testMode === 'true') {
      this.removeCookie(this.cookieName);
      return;
    }

    this.setCookie(this.cookieName, this.dataset.expiry);
  }

  getCookie(name) {
    const match = document.cookie.match(`(^|;)\\s*${name}\\s*=\\s*([^;]+)`);
    return match ? match[2] : null;
  }

  setCookie(name, expiry) {
    document.cookie = `${name}=true; max-age=${(expiry * 24 * 60 * 60)}; path=/`;
  }

  removeCookie(name) {
    document.cookie = `${name}=; max-age=0`;
  }
}
customElements.define('promo-popup', PromoPopup);
