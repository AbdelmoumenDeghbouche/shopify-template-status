  window.addEventListener('DOMContentLoaded', (event) => {
  const stickyATC = document.querySelector('#lumin-sticky-atc')
  const img = stickyATC.querySelector('.product-content img')
  const price = stickyATC.querySelector('#price-sticky')
  const btn = stickyATC.querySelector('[name="add"]')
  const btnSpinner = btn.querySelector('.loading-overlay__spinner')
  const selectField = stickyATC.querySelector('select[name="id"]')
  const threshold = document.querySelector('button[name="add"]').getBoundingClientRect().bottom + Number(stickyATC.dataset.offset)

  window.addEventListener('scroll', () => {
    if (window.scrollY > threshold) {
      stickyATC.classList.add('show')
      document.documentElement.style.paddingBottom = `${stickyATC.clientHeight}px`
      document.documentElement.style.height = 'auto'
    } else {
      stickyATC.classList.remove('show')
      document.documentElement.style.paddingBottom = '0'
    }
  })

  if (selectField) {
    selectField.addEventListener('change', () => {
      img.setAttribute('src', selectField.options[selectField.selectedIndex].dataset.img)
    })
  }
    
  document.querySelector('.product-form [name="id"]')?.addEventListener('change', (e) => {
    const value = Number(e.target.value)
    if (value) {
      selectField.value = value
    }
  })
})