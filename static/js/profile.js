document.addEventListener('DOMContentLoaded', function() {
    const passwordCell = document.getElementById('passwordCell');
    const maskedPassword = document.getElementById('maskedPassword');
    const realPassword = document.getElementById('realPassword');

    if (passwordCell && maskedPassword && realPassword) {
        passwordCell.addEventListener('mouseover', function() {
            maskedPassword.style.display = 'none';
            realPassword.style.display = 'inline-block';
        });

        passwordCell.addEventListener('mouseout', function() {
            maskedPassword.style.display = 'inline-block';
            realPassword.style.display = 'none';
        });
    }
});
