# GreenRoute
GreenRoute is a smart decision-maker for AI tasks. Instead of sending tasks to the same model and using the same amount of resources, it looks at what the task actually needs and chooses a suitable model, location, and timing. It tries to maintain the required accuracy and speed while reducing unnecessary cost, energy usage, and carbon emissions.

## Email OTP authentication

Login requires a six-digit code sent to the registered email address. Configure SMTP in the root `.env` file for real email delivery:

```env
GREENROUTE_SECRET_KEY=replace-with-a-long-random-secret
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=no-reply@example.com
```

Without `SMTP_HOST`, development mode prints the OTP in the backend terminal instead of sending email.
