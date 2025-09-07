class CartRemoveButton extends HTMLElement {
  constructor() {
    super();

    this.addEventListener('click', (event) => {
      event.preventDefault();
      const cartItems = this.closest('cart-items') || this.closest('cart-drawer-items');
      cartItems.updateQuantity(this.dataset.index, 0);
    });
  }
}

customElements.define('cart-remove-button', CartRemoveButton);

class CartItems extends HTMLElement {
  constructor() {
    super();
    this.lineItemStatusElement =
      document.getElementById('shopping-cart-line-item-status') || document.getElementById('CartDrawer-LineItemStatus');

    const debouncedOnChange = debounce((event) => {
      this.onChange(event);
    }, ON_CHANGE_DEBOUNCE_TIMER);

    this.addEventListener('change', debouncedOnChange.bind(this));
        const cartUpsellToggle = document.getElementById('cart-upsell-toggle');
    if (cartUpsellToggle) {
      cartUpsellToggle.addEventListener('change', this.onCartUpsellToggle.bind(this));
    }

  }

  cartUpdateUnsubscriber = undefined;

  connectedCallback() {
    this.cartUpdateUnsubscriber = subscribe(PUB_SUB_EVENTS.cartUpdate, (event) => {
      if (event.source === 'cart-items') {
        return;
      }
      this.onCartUpdate();
    });
        if (this.tagName !== 'CART-DRAWER-ITEMS') {
      fetch(`${routes.cart_url}.js`)
        .then((response) => response.json())
        .then((parsedState) => {
          this.updateCartUpsellToggleState();
          this.updateCartUpsellVisibility(parsedState.item_count);
        })
        .catch((e) => {
          console.error(e);
        });
    }

  }

  disconnectedCallback() {
    if (this.cartUpdateUnsubscriber) {
      this.cartUpdateUnsubscriber();
    }
  }

  onChange(event) {
    this.updateQuantity(event.target.dataset.index, event.target.value, document.activeElement.getAttribute('name'), event.target.dataset.quantityVariantId);
  }

  onCartUpdate() {
    if (this.tagName === 'CART-DRAWER-ITEMS') {
      fetch(`${routes.cart_url}?section_id=cart-drawer`)
        .then((response) => response.text())
        .then((responseText) => {
          const html = new DOMParser().parseFromString(responseText, 'text/html');
          const selectors = ['cart-drawer-items', '.cart-drawer__footer'];
          for (const selector of selectors) {
            const targetElement = document.querySelector(selector);
            const sourceElement = html.querySelector(selector);
            if (targetElement && sourceElement) {
              targetElement.replaceWith(sourceElement);
            }
          }
                    const parsedStateElement = html.querySelector('[data-cart-drawer-state]');
          const parsedState = parsedStateElement ? JSON.parse(parsedStateElement.textContent) : null;
          this.updateCartUpsellToggleState();
          if (parsedState) {
            this.updateCartUpsellVisibility(parsedState.item_count);
          }
        })
        .catch((e) => {
          console.error(e);
        });
    } else {
      fetch(`${routes.cart_url}?section_id=main-cart-items`)
        .then((response) => response.text())
        .then((responseText) => {
          const html = new DOMParser().parseFromString(responseText, 'text/html');
          const sourceQty = html.querySelector('cart-items');
          this.innerHTML = sourceQty.innerHTML;
                    const parsedStateElement = html.querySelector('[data-cart-state]');
          const parsedState = parsedStateElement ? JSON.parse(parsedStateElement.textContent) : null;
          this.updateCartUpsellToggleState();
          if (parsedState) {
            this.updateCartUpsellVisibility(parsedState.item_count);
          }

        })
        .catch((e) => {
          console.error(e);
        });
    }
  }



  updateCartUpsellToggleState() {
    const cartUpsellToggle = document.getElementById('cart-upsell-toggle');
    const scriptTag = document.querySelector('script[data-cart-upsell-variant-id]');
    const cartUpsellVariantId = scriptTag ? scriptTag.dataset.cartUpsellVariantId : '';
    const cartItems = document.querySelectorAll('.cart-item');

    const upsellItem = Array.from(cartItems).find(item => {
      const input = item.querySelector('input[data-quantity-variant-id]');
      return input && input.getAttribute('data-quantity-variant-id') === cartUpsellVariantId;
    });

    if (cartUpsellToggle && cartUpsellToggle.checked !== !!upsellItem) {
      cartUpsellToggle.checked = !!upsellItem;
    }
  }

  updateCartUpsellVisibility(itemCount) {
    const cartUpsellContainer = document.querySelector('.cart-upsell-toggle-container');
    if (cartUpsellContainer) {
      if (itemCount === 0) {
        cartUpsellContainer.classList.add('hidden');
      } else {
        cartUpsellContainer.classList.remove('hidden');
      }
    }
  }


  onCartUpsellToggle(event) {
  const scriptTag = document.querySelector('script[data-cart-upsell-variant-id]');
  const cartUpsellVariantId = scriptTag ? scriptTag.dataset.cartUpsellVariantId : '';
  const isChecked = event.target.checked;

  if (isChecked) {
    this.addUpsellProduct(cartUpsellVariantId).then(() => {
      // Fetch cart data to update progress bar
      fetch(`${routes.cart_url}.js`)
        .then((response) => response.json())
        .then((parsedState) => {
          this.updateProgressBar({
            total_price: parsedState.total_price,
            items_subtotal_price: parsedState.items_subtotal_price
          });
        })
        .catch((e) => console.error(e));
    });
  } else {
    if (!this.removingUpsellProduct) {
      this.removingUpsellProduct = true;
      this.removeUpsellProduct(cartUpsellVariantId).then(() => {
        // Fetch cart data to update progress bar
        fetch(`${routes.cart_url}.js`)
          .then((response) => response.json())
          .then((parsedState) => {
            this.updateProgressBar({
              total_price: parsedState.total_price,
              items_subtotal_price: parsedState.items_subtotal_price
            });
          })
          .catch((e) => console.error(e))
          .finally(() => {
            this.removingUpsellProduct = false;
          });
      });
    }
  }
}


  async addUpsellProduct(cartUpsellVariantId) {
    const upsellFormData = new FormData();
    upsellFormData.append('id', cartUpsellVariantId);
    upsellFormData.append('quantity', 1);

    const config = fetchConfig('javascript');
    config.headers['X-Requested-With'] = 'XMLHttpRequest';
    delete config.headers['Content-Type'];
    config.body = upsellFormData;

    const response = await fetch(`${routes.cart_add_url}`, config);
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Failed to add upsell product:', errorText);
      throw new Error('Failed to add upsell product');
    }

    this.onCartUpdate();
  }

  async removeUpsellProduct(cartUpsellVariantId) {
    const cartItems = document.querySelectorAll('.cart-item');

    const upsellItem = Array.from(cartItems).find(item => {
      const input = item.querySelector('input[data-quantity-variant-id]');
      return input && input.getAttribute('data-quantity-variant-id') === cartUpsellVariantId;
    });

    if (!upsellItem) {
      console.error('Upsell product not found in the cart.');
      return;
    }

    const upsellIndex = upsellItem.querySelector('input[data-index]').dataset.index;

    try {
      await this.updateQuantity(upsellIndex, 0, null, cartUpsellVariantId);
      this.removingUpsellProduct = false;
    } catch (error) {
      console.error('Error removing upsell product:', error);
      this.removingUpsellProduct = false;
    }
  }

  
  getSectionsToRender() {
    return [
      {
        id: 'main-cart-items',
        section: document.getElementById('main-cart-items').dataset.id,
        selector: '.js-contents',
      },
      {
        id: 'cart-icon-bubble',
        section: 'cart-icon-bubble',
        selector: '.shopify-section',
      },
      {
        id: 'cart-live-region-text',
        section: 'cart-live-region-text',
        selector: '.shopify-section',
      },
      {
        id: 'main-cart-footer',
        section: document.getElementById('main-cart-footer').dataset.id,
        selector: '.js-contents',
      },
    ];
  }

  updateQuantity(line, quantity, name, variantId) {
    this.enableLoading(line);

    const body = JSON.stringify({
      line,
      quantity,
      sections: this.getSectionsToRender().map((section) => section.section),
      sections_url: window.location.pathname,
    });

    fetch(`${routes.cart_change_url}`, { ...fetchConfig(), ...{ body } })
      .then((response) => {
        return response.text();
      })
      .then((state) => {
        const parsedState = JSON.parse(state);
        const quantityElement =
          document.getElementById(`Quantity-${line}`) || document.getElementById(`Drawer-quantity-${line}`);
        const items = document.querySelectorAll('.cart-item');

        if (parsedState.errors) {
          quantityElement.value = quantityElement.getAttribute('value');
          this.updateLiveRegions(line, parsedState.errors);
          return;
        }

        this.classList.toggle('is-empty', parsedState.item_count === 0);
        const cartDrawerWrapper = document.querySelector('cart-drawer');
        const cartFooter = document.getElementById('main-cart-footer');

        if (cartFooter) cartFooter.classList.toggle('is-empty', parsedState.item_count === 0);
        if (cartDrawerWrapper) cartDrawerWrapper.classList.toggle('is-empty', parsedState.item_count === 0);

        this.getSectionsToRender().forEach((section) => {
          const elementToReplace =
            document.getElementById(section.id).querySelector(section.selector) || document.getElementById(section.id);
          elementToReplace.innerHTML = this.getSectionInnerHTML(
            parsedState.sections[section.section],
            section.selector
          );
        });
        const updatedValue = parsedState.items[line - 1] ? parsedState.items[line - 1].quantity : undefined;
        let message = '';
        if (items.length === parsedState.items.length && updatedValue !== parseInt(quantityElement.value)) {
          if (typeof updatedValue === 'undefined') {
            message = window.cartStrings.error;
          } else {
            message = window.cartStrings.quantityError.replace('[quantity]', updatedValue);
          }
        }
        this.updateLiveRegions(line, message);

        const lineItem =
          document.getElementById(`CartItem-${line}`) || document.getElementById(`CartDrawer-Item-${line}`);
        if (lineItem && lineItem.querySelector(`[name="${name}"]`)) {
          cartDrawerWrapper
            ? trapFocus(cartDrawerWrapper, lineItem.querySelector(`[name="${name}"]`))
            : lineItem.querySelector(`[name="${name}"]`).focus();
        } else if (parsedState.item_count === 0 && cartDrawerWrapper) {
          trapFocus(cartDrawerWrapper.querySelector('.drawer__inner-empty'), cartDrawerWrapper.querySelector('a'));
        } else if (document.querySelector('.cart-item') && cartDrawerWrapper) {
          trapFocus(cartDrawerWrapper, document.querySelector('.cart-item__name'));
        }
        

          this.updateProgressBar({
    total_price: parsedState.total_price,
    items_subtotal_price: parsedState.items_subtotal_price
  });
      


        publish(PUB_SUB_EVENTS.cartUpdate, { source: 'cart-items', cartData: parsedState, variantId: variantId });
                this.updateCartUpsellToggleState();
        this.updateCartUpsellVisibility(parsedState.item_count);

      })
      .catch(() => {
        this.querySelectorAll('.loading__spinner').forEach((overlay) => overlay.classList.add('hidden'));
        const errors = document.getElementById('cart-errors') || document.getElementById('CartDrawer-CartErrors');
        errors.textContent = window.cartStrings.error;
      })
      .finally(() => {
        this.disableLoading(line);
      });
  }

updateProgressBar({ total_price, items_subtotal_price }) {
  const progressWrapper = document.getElementById('cart-progress-wrapper');
  if (!progressWrapper) return;
  
    const cartTotalCents = progressWrapper.dataset.useItemsSubtotal === 'true'
        ? items_subtotal_price
        : total_price;



  const currencyFormat = progressWrapper.dataset.currencyFormat;
  const thresholds = progressWrapper.dataset.thresholds.split(',').map(Number);
  const preGoalMessages = progressWrapper.dataset.preGoalMessages.split('||');
  const postGoalMessages = progressWrapper.dataset.postGoalMessages.split('||');
  const goalPositions = progressWrapper.dataset.goalPositions.split(',').map(Number);

  const totalThreshold = thresholds[thresholds.length - 1];
  const progressPercentage = Math.min((cartTotalCents / totalThreshold) * 100, 100);

  const progressBar = document.getElementById('cart-progress-bar');
  const goalIcons = document.querySelectorAll('.goal-icon');
  const goalMessageElement = document.querySelector('.goal-message');

  if (cartTotalCents === 0) {
    progressWrapper.style.display = 'none';
    goalMessageElement.style.display = 'none';
    progressBar.style.width = '0%'; 
  } else {
    progressWrapper.style.display = 'block';
    const previousWidth = parseFloat(progressBar.style.width) || 0;
    progressBar.style.width = `${progressPercentage}%`;

    if (progressPercentage >= 100) {
      progressWrapper.classList.add('full');
    } else {
      progressWrapper.classList.remove('full');
    }

    let nextGoalIndex = -1;
    for (let i = 0; i < thresholds.length; i++) {
      if (cartTotalCents < thresholds[i]) {
        nextGoalIndex = i;
        break;
      }
    }

/*goalIcons.forEach((goalIcon, index) => {
  const cartTotalDiff = cartTotalCents - thresholds[index];
  const goalNumber = goalIcon.dataset.index;
  
  // Select icon containers
  const iconBefore = goalIcon.querySelector(".icon-progress-before");
  const iconAfter = goalIcon.querySelector(".icon-progress-after");
  
  if (iconBefore) {
    const regularIconUrl = goalIcon.dataset.regularIcon;
    if (regularIconUrl) {
      iconBefore.innerHTML = `<img src="${regularIconUrl}" alt="Goal ${goalNumber}">`;
    }
  }
  
  if (iconAfter) {
    const reachedIconUrl = goalIcon.dataset.reachedIcon;
    if (reachedIconUrl) {
      iconAfter.innerHTML = `<img src="${reachedIconUrl}" alt="Goal ${goalNumber} Reached">`;
    }
  }
  
  // Update the goal description if available
  const description = goalIcon.querySelector(".goal-description");
  if (description && descriptions[index] !== "") {
    description.textContent = descriptions[index];
  }
});*/
    
   goalIcons.forEach((goalIcon, index) => {
      const cartTotalDiff = cartTotalCents - thresholds[index];
      const icon = goalIcon.querySelector('goal-icon');
      const goalNumber = goalIcon.dataset.index;
      
      if (icon) {
        if (cartTotalDiff < 0) {
          const regularIconUrl = goalIcon.dataset.regularIcon;
          if (regularIconUrl) {
            icon.src = regularIconUrl;
            icon.srcset = `${regularIconUrl} 50w`;
            icon.alt = `Goal ${goalNumber}`;
          }
        } else {
          const reachedIconUrl = goalIcon.dataset.reachedIcon;
          if (reachedIconUrl) {
            icon.src = reachedIconUrl;
            icon.srcset = `${reachedIconUrl} 50w`;
            icon.alt = `Goal ${goalNumber} Reached`;
          }
        }
      }
    });

    goalMessageElement.style.display = 'block';
    if (nextGoalIndex === -1) {
      const message = postGoalMessages[postGoalMessages.length - 1];
      goalMessageElement.innerHTML = message;
    } else {
      const remainingForGoal = thresholds[nextGoalIndex] - cartTotalCents;
      const remainingAmount = remainingForGoal / 100;
      const remainingAmountFormatted = this.formatCurrency(currencyFormat, remainingAmount);
      const preGoalMessageTemplate = preGoalMessages[nextGoalIndex];
      const message = preGoalMessageTemplate.replace('[x]', remainingAmountFormatted);
      goalMessageElement.innerHTML = message;
    }
  }
}

formatCurrency(currencyFormat, amount) {
  let formattedAmount = '';
  formattedAmount = currencyFormat
    .replace('{{amount}}', amount.toFixed(2)) // Standard with two decimals
    .replace('{{amount_no_decimals}}', amount.toFixed(0)) // No decimals
    .replace('{{amount_with_comma_separator}}', amount.toFixed(2).replace('.', ',')) // Replace period with comma
    .replace('{{amount_no_decimals_with_comma_separator}}', amount.toFixed(0).replace('.', ',')) // No decimals, use comma
    .replace('{{amount_with_apostrophe_separator}}', amount.toFixed(2).replace('.', "'")) // Apostrophe separator
    .replace('{{amount_no_decimals_with_space_separator}}', amount.toFixed(0).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ')) // No decimals, space
    .replace('{{amount_with_space_separator}}', amount.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ').replace('.', ',')) // Space separator
    .replace('{{amount_with_period_and_space_separator}}', amount.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ')); // Period and space
  return formattedAmount;
}


 /* updateProgressBar(cartTotal, itemCount) {
  const progressWrapper = document.getElementById('cart-progress-wrapper');

  const currencyFormat = progressWrapper.dataset.currencyFormat;
  const progressThreshold = parseInt(progressWrapper.dataset.threshold, 10);
  const preGoalMessageTemplate = progressWrapper.dataset.preGoalMessageTemplate;
  const postGoalMessage = progressWrapper.dataset.postGoalMessage;

  const progressBar = document.getElementById('cart-progress-bar');
  const goalMessageElement = document.querySelector('.goal-message');

  if (itemCount === 0 || cartTotal === 0) {
    if (progressWrapper) {
      progressWrapper.style.display = 'none';
    }
    if (goalMessageElement) {
      goalMessageElement.style.display = 'none';
    }
  } else {
    if (progressWrapper) {
      progressWrapper.style.display = 'block'; 
    }
    if (progressBar) {
      progressBar.style.display = 'block';
      const progressPercentage = Math.min((cartTotal / progressThreshold) * 100, 100); 
      progressBar.style.width = `${progressPercentage}%`;

      if (progressPercentage >= 100) {
        progressWrapper.classList.add('full');
      } else {
        progressWrapper.classList.remove('full');
      }
    }
  
    if (goalMessageElement) {
      goalMessageElement.style.display = 'block';
      let remainingForGoal = progressThreshold - cartTotal;
  
      if (remainingForGoal < 0) {
        remainingForGoal = 0;
      }

      const remainingAmount = remainingForGoal / 100;
      const remainingAmountFormatted = this.formatCurrency(currencyFormat, remainingAmount);
      const preGoalMessage = preGoalMessageTemplate.replace('[x]', remainingAmountFormatted);

      goalMessageElement.innerHTML = remainingForGoal > 0 ? preGoalMessage : postGoalMessage;
    }
  }
}

formatCurrency(currencyFormat, amount) {
  let formattedAmount = '';
  formattedAmount = currencyFormat
    .replace('{{amount}}', amount.toFixed(2)) // Standard with two decimals
    .replace('{{amount_no_decimals}}', amount.toFixed(0)) // No decimals
    .replace('{{amount_with_comma_separator}}', amount.toFixed(2).replace('.', ',')) // Replace period with comma
    .replace('{{amount_no_decimals_with_comma_separator}}', amount.toFixed(0).replace('.', ',')) // No decimals, use comma
    .replace('{{amount_with_apostrophe_separator}}', amount.toFixed(2).replace('.', "'")) // Apostrophe separator
    .replace('{{amount_no_decimals_with_space_separator}}', amount.toFixed(0).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ')) // No decimals, space
    .replace('{{amount_with_space_separator}}', amount.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ').replace('.', ',')) // Space separator
    .replace('{{amount_with_period_and_space_separator}}', amount.toFixed(2).replace(/\\B(?=(\\d{3})+(?!\\d))/g, ' ')); // Period and space
  return formattedAmount;
}*/


  updateLiveRegions(line, message) {
    const lineItemError =
      document.getElementById(`Line-item-error-${line}`) || document.getElementById(`CartDrawer-LineItemError-${line}`);
    if (lineItemError) lineItemError.querySelector('.cart-item__error-text').innerHTML = message;

    this.lineItemStatusElement.setAttribute('aria-hidden', true);

    const cartStatus =
      document.getElementById('cart-live-region-text') || document.getElementById('CartDrawer-LiveRegionText');
    cartStatus.setAttribute('aria-hidden', false);

    setTimeout(() => {
      cartStatus.setAttribute('aria-hidden', true);
    }, 1000);
  }

  getSectionInnerHTML(html, selector) {
    return new DOMParser().parseFromString(html, 'text/html').querySelector(selector).innerHTML;
  }

  enableLoading(line) {
    const mainCartItems = document.getElementById('main-cart-items') || document.getElementById('CartDrawer-CartItems');
    mainCartItems.classList.add('cart__items--disabled');

    const cartItemElements = this.querySelectorAll(`#CartItem-${line} .loading__spinner`);
    const cartDrawerItemElements = this.querySelectorAll(`#CartDrawer-Item-${line} .loading__spinner`);

    [...cartItemElements, ...cartDrawerItemElements].forEach((overlay) => overlay.classList.remove('hidden'));

    document.activeElement.blur();
    this.lineItemStatusElement.setAttribute('aria-hidden', false);
  }

  disableLoading(line) {
    const mainCartItems = document.getElementById('main-cart-items') || document.getElementById('CartDrawer-CartItems');
    mainCartItems.classList.remove('cart__items--disabled');

    const cartItemElements = this.querySelectorAll(`#CartItem-${line} .loading__spinner`);
    const cartDrawerItemElements = this.querySelectorAll(`#CartDrawer-Item-${line} .loading__spinner`);

    cartItemElements.forEach((overlay) => overlay.classList.add('hidden'));
    cartDrawerItemElements.forEach((overlay) => overlay.classList.add('hidden'));
  }
}

customElements.define('cart-items', CartItems);

if (!customElements.get('cart-note')) {
  customElements.define(
    'cart-note',
    class CartNote extends HTMLElement {
      constructor() {
        super();

        this.addEventListener(
          'change',
          debounce((event) => {
            const body = JSON.stringify({ note: event.target.value });
            fetch(`${routes.cart_update_url}`, { ...fetchConfig(), ...{ body } });
          }, ON_CHANGE_DEBOUNCE_TIMER)
        );
      }
    }
  );
}

    const cartUpdatedEvent = new CustomEvent('cartUpdated', {
      detail: {
        message: 'Cart was updated',
      }
    });
    document.dispatchEvent(cartUpdatedEvent);
