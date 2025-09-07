customElements.define('sticky-product-form', class StickyProductForm extends HTMLElement {
    constructor() {
      super();
    }

    connectedCallback() {
      this.productForm = document.querySelector('product-form');

      this.productStickyForm = document.querySelector('.product--sticky-form');
      this.productFormBounds = {};

      this.onScrollHandler = this.onScroll.bind(this);
      window.addEventListener('scroll', this.onScrollHandler, false);

      this.createObserver();
    }

    disconnectedCallback() {
      window.removeEventListener('scroll', this.onScrollHandler);
    }

    createObserver() {
      let observer = new IntersectionObserver((entries, observer) => {
        this.productFormBounds = entries[0].isIntersecting;
      });
      observer.observe(this.productForm);
    }

    onScroll() {
      this.productFormBounds ? requestAnimationFrame(this.hide.bind(this)) : requestAnimationFrame(this.reveal.bind(this));
    }

    hide() {
      if(this.productStickyForm.classList.contains('product--sticky-form__active')) {
        this.productStickyForm.classList.remove('product--sticky-form__active');
        this.productStickyForm.classList.add('product--sticky-form__inactive');
      }
    }

    reveal() {
      if(this.productStickyForm.classList.contains('product--sticky-form__inactive')) {
        this.productStickyForm.classList.add('product--sticky-form__active');
        this.productStickyForm.classList.remove('product--sticky-form__inactive');
      }
    }
  });