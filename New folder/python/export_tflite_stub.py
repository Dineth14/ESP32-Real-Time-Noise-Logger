"""
Stub: Convert a trained Keras model to TFLite and optionally quantize for micro.
This is a placeholder: filling this out requires TensorFlow installed locally.
"""

def export_tflite(model, out_path='model.tflite'):
    try:
        import tensorflow as tf
    except Exception as e:
        raise RuntimeError('TensorFlow not available in this environment: ' + str(e))
    # Convert
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()
    with open(out_path, 'wb') as f:
        f.write(tflite_model)
    print('Wrote', out_path)
