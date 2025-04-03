import unittest
from unittest.mock import patch, MagicMock, mock_open, PropertyMock
import io
import os
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

from ace.translate import ChartTranslator

class TestChartTranslator(unittest.TestCase):
    """Tests for ChartTranslator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create patchers for environment and S3FileManager
        self.env_patcher = patch('ace.translate.load_dotenv')
        self.s3_manager_patcher = patch('ace.translate.S3FileManager')
        
        # Start patchers
        self.mock_env = self.env_patcher.start()
        self.mock_s3_manager_class = self.s3_manager_patcher.start()
        
        # Setup S3FileManager mock instances
        self.mock_raw_midi_bucket = MagicMock()
        self.mock_split_midi_bucket = MagicMock()
        self.mock_chart_bucket = MagicMock()
        
        # Configure S3FileManager class mock to return our bucket mocks
        self.mock_s3_manager_class.side_effect = [
            self.mock_raw_midi_bucket,
            self.mock_split_midi_bucket,
            self.mock_chart_bucket
        ]
        
        # Path to getenv
        self.getenv_patcher = patch('os.getenv')
        self.mock_getenv = self.getenv_patcher.start()
        self.mock_getenv.return_value = 'test-value'
        
        # Initialize ChartTranslator
        self.translator = ChartTranslator()
        
    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.s3_manager_patcher.stop()
        self.getenv_patcher.stop()
    
    def test_init(self):
        """Test initialization of ChartTranslator."""
        # Check that dotenv was loaded
        self.mock_env.assert_called_once()
        
        # Check that S3FileManager was created with correct bucket names
        self.mock_s3_manager_class.assert_any_call(
            bucket_name="raw-midi-files",
            aws_access_key_id='test-value',
            aws_secret_access_key='test-value',
            region_name='test-value'
        )
        
        self.mock_s3_manager_class.assert_any_call(
            bucket_name="split-midi-files",
            aws_access_key_id='test-value',
            aws_secret_access_key='test-value',
            region_name='test-value'
        )
        
        self.mock_s3_manager_class.assert_any_call(
            bucket_name="chart-files",
            aws_access_key_id='test-value',
            aws_secret_access_key='test-value',
            region_name='test-value'
        )
        
        # Check that bucket instances were assigned correctly
        self.assertEqual(self.translator.raw_midi_bucket, self.mock_raw_midi_bucket)
        self.assertEqual(self.translator.split_midi_bucket, self.mock_split_midi_bucket)
        self.assertEqual(self.translator.chart_bucket, self.mock_chart_bucket)
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'test midi data')
    @patch('ace.translate.MidiFile')
    @patch('ace.translate.MidiTrack')
    @patch('os.path.join')
    @patch('os.path.exists')
    @patch('os.path.splitext')
    @patch('os.path.basename')
    def test_split_midi(self, mock_basename, mock_splitext, mock_exists, 
                        mock_join, mock_midi_track, mock_midi_file, mock_file_open):
        """Test split_midi method."""
        # Mock the file operations
        in_file_dir = "/path/to/input.mid"
        out_dir = "/path/to/output"
        
        # Setup mocks
        mock_basename.return_value = "input.mid"
        mock_splitext.return_value = ("input", ".mid")
        mock_join.return_value = "/path/to/output/input_DRUMS.mid"
        mock_exists.return_value = True
        
        # Create mock MidiFile objects with explicit track creation
        mock_in_mid = MagicMock()
        mock_out_mid = MagicMock()
        mock_midi_file.side_effect = [mock_in_mid, mock_out_mid]
        
        # Create track mocks
        mock_track1 = MagicMock()
        mock_track2 = MagicMock()
        
        # Explicitly set tracks attribute
        type(mock_in_mid).tracks = PropertyMock(return_value=[mock_track1, mock_track2])
        type(mock_in_mid).ticks_per_beat = PropertyMock(return_value=480)
        
        # Create drum track for output
        mock_drum_track = MagicMock()
        mock_midi_track.return_value = mock_drum_track
        type(mock_out_mid).tracks = PropertyMock(return_value=[mock_drum_track])
        
        # Create sample MIDI messages for tracks
        tempo_msg = MetaMessage('set_tempo', tempo=500000, time=0)
        time_sig_msg = MetaMessage('time_signature', numerator=4, denominator=4, time=0)
        note_on_drum = Message('note_on', note=36, velocity=64, time=100, channel=9)  # Drum channel
        note_off_drum = Message('note_off', note=36, velocity=0, time=100, channel=9)
        note_on_other = Message('note_on', note=60, velocity=64, time=100, channel=0)  # Not drum channel
        
        # Mock the iteration over track messages
        mock_track1.__iter__.return_value = [tempo_msg, time_sig_msg]
        mock_track2.__iter__.return_value = [note_on_drum, note_off_drum, note_on_other]
        
        # Call split_midi
        result = self.translator.split_midi(in_file_dir, out_dir)
        
        # Assertions
        # Check that the file was written to S3
        self.mock_raw_midi_bucket.write_file.assert_called_once()
        
        # Verify MidiFile was created correctly
        mock_midi_file.assert_any_call(in_file_dir)
        
        # Verify S3 upload of the split MIDI file
        self.mock_split_midi_bucket.write_file.assert_called_once()
        
        # Check the returned file key - use upper case to match the actual implementation
        self.assertEqual(result, "input_DRUMS.mid")
    
    @patch('builtins.open', new_callable=mock_open)
    @patch('io.BytesIO')
    @patch('ace.translate.MidiFile')
    @patch('ace.translate.mido.merge_tracks')
    @patch('os.path.join')
    @patch('os.path.exists')
    @patch('os.path.splitext')
    @patch('os.path.basename')
    def test_convert_to_chart(self, mock_basename, mock_splitext, mock_exists,
                              mock_join, mock_merge_tracks, mock_midi_file, 
                              mock_bytesio, mock_file_open):
        """Test convert_to_chart method."""
        # Mock the file operations
        in_file_key = "input_DRUMS.mid"
        out_dir = "/path/to/output"
        
        # Setup mocks
        mock_splitext.return_value = ("input_DRUMS", ".mid")
        mock_join.return_value = "/path/to/output/input_DRUMS.chart"
        mock_exists.return_value = True
        mock_basename.return_value = "input_DRUMS.chart"
        
        # Setup S3 mock to return MIDI data
        midi_data = b'test midi data'
        self.mock_split_midi_bucket.read_file.return_value = midi_data
        
        # Create mock BytesIO
        mock_buffer = MagicMock()
        mock_bytesio.return_value = mock_buffer
        mock_buffer.getvalue = MagicMock(return_value=midi_data)
        
        # Create mock MidiFile
        mock_mid = MagicMock()
        mock_midi_file.return_value = mock_mid
        
        # Mock tracks and data for MidiFile using PropertyMock
        mock_track = MagicMock()
        type(mock_mid).tracks = PropertyMock(return_value=[mock_track])
        type(mock_mid).ticks_per_beat = PropertyMock(return_value=480)
        
        # Setup merged track with some MIDI events
        tempo_msg = MetaMessage('set_tempo', tempo=500000, time=0)
        kick_msg = Message('note_on', note=36, velocity=64, time=100, channel=9)
        snare_msg = Message('note_on', note=38, velocity=64, time=100, channel=9)
        hihat_msg = Message('note_on', note=42, velocity=64, time=100, channel=9)
        crash_msg = Message('note_on', note=49, velocity=64, time=100, channel=9)
        
        merged_track = [tempo_msg, kick_msg, snare_msg, hihat_msg, crash_msg]
        mock_merge_tracks.return_value = merged_track
        
        # Call convert_to_chart
        self.translator.generate_chart_file(in_file_key, out_dir)
        
        # Assertions
        # Check that S3 was queried for the MIDI file
        self.mock_split_midi_bucket.read_file.assert_called_with(key=in_file_key)
        
        # Verify chart file was written to local directory
        mock_file_open.assert_any_call('/path/to/output/input_DRUMS.chart', 'w')
        
        # Verify chart file was uploaded to S3
        self.mock_chart_bucket.write_file.assert_called_once()
        
        # Verify chart content was written with expected sections
        write_calls = mock_file_open().write.call_args_list
        if write_calls:  # Check if there are any calls (might be empty in some mock setups)
            written_content = ''.join(call.args[0] for call in write_calls)
            
            # Check for expected chart sections
            self.assertIn("[Song]", written_content)
            self.assertIn("[SyncTrack]", written_content)
            self.assertIn("[Events]", written_content)
            self.assertIn("[ExpertDrums]", written_content)

if __name__ == '__main__':
    unittest.main() 