from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtCore import Qt
from src.view.generated_ui.camera_stream_widget_ui import Ui_CameraStream
import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst

Gst.init(None)


class CameraStream(QWidget, Ui_CameraStream):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        self.pipeline = None
        self.sink = None

    def init_gstreamer(self, port):
        # GStreamer setup
        self.pipeline = Gst.parse_launch(
            f"udpsrc port={port} ! h264parse ! v4l2h264dec ! videoconvert ! videoscale ! video/x-raw, width=400, height=400, format=RGB ! queue max-size-buffers=1 leaky=downstream ! appsink name=sink sync=false"
        )
        self.sink = self.pipeline.get_by_name("sink")
        self.sink.set_property("emit-signals", True)
        self.sink.connect("new-sample", self.on_new_sample)

    def on_new_sample(self, sink):
        sample = sink.emit("pull-sample")
        buf = sample.get_buffer()
        caps = sample.get_caps()
        width = caps.get_structure(0).get_value("width")
        height = caps.get_structure(0).get_value("height")

        # Extract raw video data
        data = buf.extract_dup(0, buf.get_size())
        image = QImage(data, width, height, QImage.Format_RGB888)

        # Display the frame in the QLabel
        self.stream.setPixmap(QPixmap.fromImage(image))
        return Gst.FlowReturn.OK

    def start_stream(self):
        self.pipeline.set_state(Gst.State.PLAYING)
        self.stream.setText("Waiting for stream...")

    def stop_stream(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.stream.setText("Stream stopped")
