#include <Wire.h>
#include <MPU6050.h>
#include "esp_timer.h"
#include <math.h>

#define ACCEL_SCALE_FACTOR 8192.0f
#define SAMPLE_PERIOD_US 20000
#define WINDOW_SIZE 20
#define OVERLAP_SIZE 10

static const float W[7] = {
  -0.00165011f,
  -0.00710379f,
  -0.01440110f,
  -0.00343501f,
  -0.00081765f,
  -0.04453173f,
   0.00366878f
};

static const float B = 1.8944849323f;

MPU6050 mpu;

static float az_buf[WINDOW_SIZE];
static volatile int idx = 0;
static volatile bool janela_pronta = false;

static portMUX_TYPE mux = portMUX_INITIALIZER_UNLOCKED;

static esp_timer_handle_t timer_coleta;

// ----------------------------
// Funções de features (az)
// ----------------------------

float calc_min(const float* v, int n) {
  float mn = v[0];
  for (int i = 1; i < n; i++) if (v[i] < mn) mn = v[i];
  return mn;
}

float calc_max(const float* v, int n) {
  float mx = v[0];
  for (int i = 1; i < n; i++) if (v[i] > mx) mx = v[i];
  return mx;
}

float calc_mean(const float* v, int n) {
  float s = 0.0f;
  for (int i = 0; i < n; i++) s += v[i];
  return s / (float)n;
}

float calc_std_pop(const float* v, int n) {
  float m = calc_mean(v, n);
  float s2 = 0.0f;
  for (int i = 0; i < n; i++) {
    float d = v[i] - m;
    s2 += d * d;
  }
  return sqrtf(s2 / (float)n);
}

float calc_rms(const float* v, int n) {
  float s = 0.0f;
  for (int i = 0; i < n; i++) s += v[i] * v[i];
  return sqrtf(s / (float)n);
}

float calc_energy_sum(const float* v, int n) {
  float s = 0.0f;
  for (int i = 0; i < n; i++) s += v[i] * v[i];
  return s;
}

float calc_ptp(const float* v, int n) {
  return calc_max(v, n) - calc_min(v, n);
}

float calc_dft_mag_k(const float* v, int n, int k) {
  float re = 0.0f, im = 0.0f;
  for (int i = 0; i < n; i++) {
    float a = 2.0f * PI * (float)k * (float)i / (float)n;
    re += v[i] * cosf(a);
    im -= v[i] * sinf(a);
  }
  return sqrtf(re * re + im * im);
}

// ----------------------------
// Controle de buffer
// ----------------------------

void reset_buffer() {
  portENTER_CRITICAL(&mux);
  for (int i = 0; i < WINDOW_SIZE; i++) az_buf[i] = 0.0f;
  idx = 0;
  janela_pronta = false;
  portEXIT_CRITICAL(&mux);
}
void aplicar_overlap() {
  portENTER_CRITICAL(&mux);
  for (int i = 0; i < OVERLAP_SIZE; i++) {
    az_buf[i] = az_buf[i + (WINDOW_SIZE - OVERLAP_SIZE)];
  }
  idx = OVERLAP_SIZE;
  janela_pronta = false;
  portEXIT_CRITICAL(&mux);
}

// ----------------------------
// Coleta periódica (timer)
// ----------------------------

void coletar(void* arg) {
  int16_t ax_raw, ay_raw, az_raw;
  mpu.getAcceleration(&ax_raw, &ay_raw, &az_raw);

  portENTER_CRITICAL_ISR(&mux);

  if (idx < WINDOW_SIZE) {
    az_buf[idx] = (float)az_raw / ACCEL_SCALE_FACTOR;
    idx++;
    if (idx >= WINDOW_SIZE) janela_pronta = true;
  }

  portEXIT_CRITICAL_ISR(&mux);
}

// ----------------------------
// Setup
// ----------------------------

void setup() {
  Serial.begin(115200);
  Wire.begin();

  mpu.initialize();
  if (!mpu.testConnection()) {
    Serial.println("MPU6050 nao conectada!");
    while (1) { }
  }

  mpu.setFullScaleAccelRange(MPU6050_ACCEL_FS_4);
  Serial.println("MPU6050 conectada. Aguardando dados...");

  reset_buffer();

  const esp_timer_create_args_t args = {
    .callback = &coletar,
    .arg = NULL,
    .dispatch_method = ESP_TIMER_TASK,
    .name = "coleta_50hz"
  };

  esp_timer_create(&args, &timer_coleta);
  esp_timer_start_periodic(timer_coleta, SAMPLE_PERIOD_US);
}
// ----------------------------
// Loop
// ----------------------------

void loop() {

  if (!janela_pronta) return;

  float az[WINDOW_SIZE];

  portENTER_CRITICAL(&mux);
  for (int i = 0; i < WINDOW_SIZE; i++) az[i] = az_buf[i];
  janela_pronta = false;  // evita reprocessar a mesma janela
  portEXIT_CRITICAL(&mux);

  float az_std    = calc_std_pop(az, WINDOW_SIZE);
  float az_ptp    = calc_ptp(az, WINDOW_SIZE);
  float az_fft_5  = calc_dft_mag_k(az, WINDOW_SIZE, 5);
  float az_max    = calc_max(az, WINDOW_SIZE);
  float az_rms    = calc_rms(az, WINDOW_SIZE);
  float az_energy = calc_energy_sum(az, WINDOW_SIZE);
  float az_min    = calc_min(az, WINDOW_SIZE);

  float fx = B
    + W[0] * az_std
    + W[1] * az_ptp
    + W[2] * az_fft_5
    + W[3] * az_max
    + W[4] * az_rms
    + W[5] * az_energy
    + W[6] * az_min;
if (fx < 0.0f) {

    esp_timer_stop(timer_coleta);

    Serial.println();
    Serial.println(">>> Movimento reconhecido!");
    Serial.printf("az_std    = %.6f\n", az_std);
    Serial.printf("az_ptp    = %.6f\n", az_ptp);
    Serial.printf("az_fft_5  = %.6f\n", az_fft_5);
    Serial.printf("az_max    = %.6f\n", az_max);
    Serial.printf("az_rms    = %.6f\n", az_rms);
    Serial.printf("az_energy = %.6f\n", az_energy);
    Serial.printf("az_min    = %.6f\n", az_min);
    Serial.printf("f(x)      = %.6f\n", fx);

    delay(1000);

    reset_buffer();
    esp_timer_start_periodic(timer_coleta, SAMPLE_PERIOD_US);
    return;
  }

  aplicar_overlap();
}
