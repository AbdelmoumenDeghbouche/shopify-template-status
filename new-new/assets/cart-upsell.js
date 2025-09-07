 (function () {  
    async function insertSectionCartDrawer() {
      if (document.querySelector('#CartDrawer .cart-drawer-items-wrapper')) return

      var cartDrawerItems = document.querySelector('#CartDrawer cart-drawer-items')
      if (!cartDrawerItems) return

      if (cartDrawerItems.classList.contains('is-empty')) return

      var wrapper = document.createElement('div')
      wrapper.classList.add('cart-drawer-items-wrapper')
      cartDrawerItems.parentNode.insertBefore(wrapper, cartDrawerItems)
      wrapper.appendChild(cartDrawerItems)

      const upsells = document.querySelector('#cart-drawer-upsell-wrapper')
      wrapper.insertAdjacentHTML('beforeend', upsells.innerHTML)
 
      if (!document.querySelector('.cart-drawer-upsell-list li')) {
        document.querySelector('#cart-drawer-upsell').remove()  
      }
    }
    insertSectionCartDrawer()

  /*  async function insertSectionCartPage() {
      const cartItems = document.querySelector('cart-items')
      if (!cartItems) return

      const existingUpsells = document.querySelector('#MainContent #cart-drawer-upsell')
      if (existingUpsells) {
        existingUpsells.remove()
      }

      const upsells = document.querySelector('#cart-drawer-upsell-wrapper')
      cartItems.querySelector('.page-width').insertAdjacentHTML('beforeend', upsells.innerHTML)

      if (!document.querySelector('.cart-drawer-upsell-list li')) {
        document.querySelector('#cart-drawer-upsell').remove()  
      }
    }
    insertSectionCartPage() */
    
    window.onChangeKsUpsellVariantSelector = function( select, event) {
      event.preventDefault()
      const imgSrc = select.options[select.selectedIndex].dataset.variantImg

      if (imgSrc) {
        const img = select.closest('.cart-drawer-upsell-list-item').querySelector('.cart-drawer-upsell-list-item-left img')
        img.src = imgSrc
      }
    }

    function listenCartDrawer() {
      const element = document.querySelector('cart-drawer')
      if (!element) return
  
      let timer 
       
      const observer = new MutationObserver((mutations) => { 
        if (timer) clearTimeout(timer)

        timer = setTimeout(async () => {
          const respoonse = await fetch(window.location.href)
          const text = await respoonse.text()
          const newDocument = new DOMParser().parseFromString(text, 'text/html')

          document.querySelector('#cart-drawer-upsell-wrapper')
            .replaceWith(newDocument.querySelector('#cart-drawer-upsell-wrapper'))
 
            insertSectionCartDrawer()
        }, 250)
      })

      observer.observe(element, {  
        attributes: true, 
        childList: true, 
        subtree: true
      });
    }
    listenCartDrawer()

    function listenCartPage() {
      const element = document.querySelector('#MainContent .cart__items')
      if (!element) return

      let timer
      
      const observer = new MutationObserver((mutations) => { 
        if (timer) clearTimeout(timer)

        timer = setTimeout(async () => {
          const respoonse = await fetch(window.location.href)
          const text = await respoonse.text()
          const newDocument = new DOMParser().parseFromString(text, 'text/html')

          document.querySelector('#cart-drawer-upsell-wrapper')
            .replaceWith(newDocument.querySelector('#cart-drawer-upsell-wrapper'))

            insertSectionCartPage()
        }, 250)
      })

      observer.observe(element, { 
        attributes: true, 
        childList: true, 
        subtree: true
      });
    }
    listenCartPage()
  })();