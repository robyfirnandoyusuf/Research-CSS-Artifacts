<?php
use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\SMTP;
use PHPMailer\PHPMailer\Exception;

require 'vendor/autoload.php';

$mail = new PHPMailer(true);

try {
    $subject = "test";
    $headers = "cok";
    $message = "test";

    $mail->SMTPDebug = SMTP::DEBUG_SERVER;
    $mail->isSMTP();
    $mail->Host       = 'smtp.gmail.com';
    $mail->SMTPAuth   = true;
    $mail->Username   = 'nandoapuesto19@gmail.com';
    $mail->Password   = 'gvun qeoq spmv nkao';
    $mail->SMTPSecure = 'tls';
    $mail->Port       = 587;

    $mail->setFrom('nandoapuesto19@gmail.com', 'Mailer');
    // $mail->addAddress('micinware.blackcat@outlook.com', 'Heker');
     $mail->addAddress('admin@test.mailu.io', 'Heker');
    //$mail->addAddress('robyfirnando@naver.com', 'Heker');


    $mail->isHTML(true);
    $mail->Subject = $subject;
    $mail->Body = file_get_contents('../confirm.html');

    $mail->send();
    echo 'Message has been sent';
} catch (Exception $e) {
    echo "Message could not be sent. Mailer Error: {$mail->ErrorInfo}";
}
