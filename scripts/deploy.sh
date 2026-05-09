set -e

echo "Розпочинаємо розгортання MyWebApp..."

echo "Встановлення системних залежностей..."
apt-get update
apt-get install -y python3 python3-venv python3-pip mariadb-server nginx sudo curl

echo "Створення користувачів системи..."

create_human_user() {
    local username=$1
    if ! id -u "$username" > /dev/null 2>&1; then
        useradd -m -s /bin/bash "$username"
        echo "$username:12345678" | chpasswd
        chage -d 0 "$username"
    fi
}

create_human_user "student"
create_human_user "teacher"
create_human_user "operator"

usermod -aG sudo student
usermod -aG sudo teacher

cat <<EOF > /etc/sudoers.d/operator_mywebapp
operator ALL=(ALL) NOPASSWD: /bin/systemctl start mywebapp.service, /bin/systemctl stop mywebapp.service, /bin/systemctl restart mywebapp.service, /bin/systemctl status mywebapp.service, /bin/systemctl reload nginx
EOF
chmod 440 /etc/sudoers.d/operator_mywebapp

if ! id -u "app" > /dev/null 2>&1; then
    useradd -r -s /usr/sbin/nologin app
fi

echo "Налаштування MariaDB..."
systemctl start mariadb
systemctl enable mariadb
mysql -u root -e "CREATE DATABASE IF NOT EXISTS mywebapp_db;"
mysql -u root -e "CREATE USER IF NOT EXISTS 'mywebapp'@'localhost' IDENTIFIED BY 'password';"
mysql -u root -e "GRANT ALL PRIVILEGES ON mywebapp_db.* TO 'mywebapp'@'localhost';"
mysql -u root -e "FLUSH PRIVILEGES;"

echo "Підготовка директорії проєкту..."
PROJECT_DIR="/opt/mywebapp_project"
mkdir -p "$PROJECT_DIR"
cp -r ./* "$PROJECT_DIR/"
chown -R app:app "$PROJECT_DIR"

echo "Встановлення Python-залежностей..."
sudo -u app bash -c "python3 -m venv $PROJECT_DIR/venv"
sudo -u app bash -c "$PROJECT_DIR/venv/bin/pip install -r $PROJECT_DIR/requirements.txt"
echo "Налаштування Systemd..."
cp "$PROJECT_DIR/configs/mywebapp.service" /etc/systemd/system/mywebapp.service
systemctl daemon-reload
systemctl enable mywebapp.service
systemctl start mywebapp.service

echo "Налаштування Nginx..."
cp "$PROJECT_DIR/configs/nginx.conf" /etc/nginx/sites-available/mywebapp
ln -sf /etc/nginx/sites-available/mywebapp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl reload nginx

echo "Створення gradebook..."
echo "20" > /home/student/gradebook
chown student:student /home/student/gradebook
chmod 644 /home/student/gradebook

echo "Блокування дефолтного користувача..."
if [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "student" ] && [ "$SUDO_USER" != "teacher" ]; then
    usermod -L "$SUDO_USER"
    echo "Користувач $SUDO_USER заблокований."
fi

echo "Розгортання успішно завершено!"

echo "Налаштування UFW..."
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp  
ufw allow 80/tcp  
ufw --force enable