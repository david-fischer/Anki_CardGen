const openModalButtons = document.querySelectorAll('[data-modal-target]')
const closeModalButtons = document.querySelectorAll('[data-close-button]')
const overlay = document.getElementById('overlay')

openModalButtons.forEach(button => {
button.onclick = () => {
  openModal(document.querySelector(button.dataset.modalTarget))
}
})

overlay.onclick = () => {
const modals = document.querySelectorAll('.modal.active')
modals.forEach(modal => {
  closeModal(modal)
})
}


closeModalButtons.forEach(button => {
button.onclick = () => {
  const modal = button.closest('.modal')
  closeModal(modal)
}
})


function openModal(modal) {
if (modal == null) return
modal.classList.add('active')
overlay.classList.add('active')
}

function closeModal(modal) {
if (modal == null) return
modal.classList.remove('active')
overlay.classList.remove('active')
}
