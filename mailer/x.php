<?php
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

require 'vendor/autoload.php';

$mail = new PHPMailer(true);

try {
    $subject = $_REQUEST['subject'];
    $headers = $_REQUEST['headers'];
    $message = $_REQUEST['message'];

    $mail->SMTPDebug = SMTP::DEBUG_SERVER;
    $mail->isSMTP();
    $mail->Host       = 'smtp.gmail.com';
    $mail->SMTPAuth   = true;
    $mail->Username   = 'zuyun49@gmail.com';
    $mail->Password   = 'huen ndyo itsu quui';
    $mail->SMTPSecure = 'tls';
    $mail->Port       = 587;

    $mail->setFrom('zuyun49@gmail.com', 'Mailer');
    $mail->addAddress('luonicky90@gmail.com', 'Heker');

    $mail->isHTML(true);
    $mail->Subject = $subject;
    $mail->Body    = $message;

    $mail->send();
    echo 'Message has been sent';
} catch (Exception $e) {
    echo "Message could not be sent. Mailer Error: {$mail->ErrorInfo}";
}