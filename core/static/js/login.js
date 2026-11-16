document.addEventListener('DOMContentLoaded', () => {
    const passwordInput = document.getElementById('id_password');
    const toggleButton = document.querySelector('.alternar-senha');

    if (!passwordInput || !toggleButton) {
        return;
    }

    toggleButton.addEventListener('click', () => {
        const revealPassword = passwordInput.type === 'password';
        passwordInput.type = revealPassword ? 'text' : 'password';
        toggleButton.textContent = revealPassword ? 'Ocultar' : 'Mostrar';
        toggleButton.setAttribute('aria-pressed', String(revealPassword));
    });
});
