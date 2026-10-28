"""
Train genuine MobileNetV2 Deep Learning classifier on authentic PlantVillage dataset.
Generates genuine .keras, .h5, class_labels.json, and evaluation plots in reports/.
"""
import os
import json
from pathlib import Path

# Force KERAS_HOME inside the workspace to avoid Windows sandbox permission issues
BASE_DIR = Path(__file__).resolve().parents[1]
os.environ["KERAS_HOME"] = str(BASE_DIR / ".keras")
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models

DATASET_DIR = BASE_DIR / "dataset"
TRAIN_DIR = DATASET_DIR / "train"
TEST_DIR = DATASET_DIR / "test"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

IMG_SIZE = (224, 224)
BATCH_SIZE = 16

print("==> Loading genuine dataset splits...")
train_ds = tf.keras.utils.image_dataset_from_directory(
    str(TRAIN_DIR),
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='categorical',
    shuffle=True,
    seed=42
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    str(TEST_DIR),
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    label_mode='categorical',
    shuffle=False
)

class_names = train_ds.class_names
print("Classes:", class_names)
labels_dict = {i: name for i, name in enumerate(class_names)}
with open(MODELS_DIR / "class_labels.json", "w", encoding="utf-8") as f:
    json.dump(labels_dict, f, indent=2)
print("Saved class labels mapping.")

# Data augmentation layers for model generalization
data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal_and_vertical"),
    layers.RandomRotation(0.15),
    layers.RandomZoom(0.1),
    layers.RandomContrast(0.1),
])

# Transfer learning backbone
base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights='imagenet'
)
base_model.trainable = False

inputs = tf.keras.Input(shape=(224, 224, 3))
x = data_augmentation(inputs)
x = layers.Rescaling(1.0 / 255.0)(x)
x = base_model(x, training=False)
x = layers.GlobalAveragePooling2D()(x)
x = layers.BatchNormalization()(x)
x = layers.Dense(128, activation='relu')(x)
x = layers.Dropout(0.3)(x)
outputs = layers.Dense(len(class_names), activation='softmax')(x)

model = models.Model(inputs=inputs, outputs=outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

print("==> Training MobileNetV2 on authentic images (10 epochs)...")
epochs = 10
history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=epochs,
    verbose=1
)

# Fine-tuning: unfreeze top 20 layers for higher accuracy
print("==> Fine-tuning top convolutional layers (5 epochs)...")
base_model.trainable = True
for layer in base_model.layers[:-20]:
    layer.trainable = False

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

fine_history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=5,
    verbose=1
)

# Save artifacts
h5_path = MODELS_DIR / "plant_disease_model.h5"
keras_path = MODELS_DIR / "plant_disease_model.keras"

model.save(str(h5_path))
model.save(str(keras_path))
print(f"Model successfully saved to {keras_path} ({round(os.path.getsize(keras_path)/(1024*1024), 2)} MB)")

# Generate and save publication-grade training graphs for viva defense
import matplotlib.pyplot as plt

acc = history.history['accuracy'] + fine_history.history['accuracy']
val_acc = history.history['val_accuracy'] + fine_history.history['val_accuracy']
loss = history.history['loss'] + fine_history.history['loss']
val_loss = history.history['val_loss'] + fine_history.history['val_loss']

plt.figure(figsize=(12, 5))
plt.subplot(1, 2, 1)
plt.plot(acc, label='Train Accuracy', color='#0B5037', linewidth=2.5)
plt.plot(val_acc, label='Validation Accuracy', color='#2E7D32', linestyle='--', linewidth=2.5)
plt.title('MobileNetV2 Transfer Learning Accuracy', fontsize=12, fontweight='bold')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.grid(True, alpha=0.3)
plt.legend(loc='lower right')

plt.subplot(1, 2, 2)
plt.plot(loss, label='Train Loss', color='#C62828', linewidth=2.5)
plt.plot(val_loss, label='Validation Loss', color='#E53935', linestyle='--', linewidth=2.5)
plt.title('MobileNetV2 Loss (Categorical Crossentropy)', fontsize=12, fontweight='bold')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.grid(True, alpha=0.3)
plt.legend(loc='upper right')

plt.tight_layout()
plot_path = REPORTS_DIR / "training_performance_curves.png"
plt.savefig(str(plot_path), dpi=200)
print(f"Saved evaluation curves to {plot_path}")
