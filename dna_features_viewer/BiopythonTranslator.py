from .GraphicRecord import GraphicRecord
from .CircularGraphicRecord import CircularGraphicRecord
from .GraphicFeature import GraphicFeature
from Bio import SeqIO

class BiopythonTranslator:
    """A translator from SeqRecords to dna_features_viewer GraphicRecord.

    This can be subclassed to create custom "themes" (see the example
    ``custom_biopython_translator.py`` in the docs).

    Parameters
    ----------

    features_filters
      List of filters (some_biopython_feature) => True/False.
      Only features passing all the filters are kept.
      This only works if you haven't redefined ``compute_filtered_features``

    features_properties
      A function (feature)=> properties_dict

    """
    default_feature_color = "#7245dc"
    graphic_record_parameters = {}
    ignored_features_types = ()
    max_label_length = 50

    def __init__(self, features_filters=(), features_properties=None):
        self.features_filters = features_filters
        self.features_properties = features_properties

    def compute_feature_color(self, feature):
        """Compute a color for this feature.

        If the feature has a ``color`` qualifier it will be used. Otherwise,
        the classe's ``default_feature_color`` is used.

        To change the behaviour, create a subclass of ``BiopythonTranslator``
        and overwrite this method.
        """
        return feature.qualifiers.get("color", self.default_feature_color)

    def compute_feature_fontdict(self, feature):
        """Compute a font dict for this feature.
        """
        return None

    def compute_feature_box_linewidth(self, feature):
        """Compute a font dict for this feature.
        """
        return 1

    def compute_filtered_features(self, features):
        return [
            f for f in features
            if all([fl(f) for fl in self.features_filters])
            and f.type not in self.ignored_features_types
        ]

    @classmethod
    def compute_feature_label(cls, feature):
        """Gets the 'label' of the feature.

        This method looks for the first non-empty qualifier of the feature
        in this order ``label``, ``source``, ``locus_tag``, ``note``, which
        means that you can provide a label with, for instance
        ``feature.qualifiers['note'] = 'some note'``.

        To change the behaviour, create a subclass of ``BiopythonTranslator``
        and overwrite this method.
        """
        result = feature.type
        for key in ["label", "source", "locus_tag", "note"]:
            if key in feature.qualifiers:
                result = feature.qualifiers[key]
                break
        if isinstance(result, list):
            result = "|".join(result)
        else:
            result = result
        if len(result) > cls.max_label_length:
            result = result[:cls.max_label_length] + '...'
        return result

    @staticmethod
    def compute_feature_html(feature):
        """Gets the 'label' of the feature."""
        result = feature.type
        for key in ["note", "locus_tag", "label", "source"]:
            if key in feature.qualifiers:
                result = feature.qualifiers[key]

                break
        if isinstance(result, list):
            return "|".join(result)
        else:
            return result


    def translate_feature(self, feature):
        """Translate a Biopython feature into a Dna Features Viewer feature."""
        properties = dict(
            label=self.compute_feature_label(feature),
            color=self.compute_feature_color(feature),
            html=self.compute_feature_html(feature),
            fontdict=self.compute_feature_fontdict(feature),
            box_linewidth=self.compute_feature_box_linewidth(feature)
        )
        if self.features_properties is not None:
            other_properties = self.features_properties(feature)

        else:
            other_properties = {}
        properties.update(other_properties)

        return GraphicFeature(start=feature.location.start,
                              end=feature.location.end,
                              strand=feature.location.strand,
                              **properties)

    def translate_record(self, record, record_class=None):
        """Create a new GraphicRecord from a BioPython Record object.

        Parameters
        ----------

        record
          A BioPython Record object or the path to a Genbank file.

        record_class
          The graphic record class to use, e.g. GraphicRecord (default) or
          CircularGraphicRecord. Strings 'circular' and 'linear' can also be
          provided.
        """
        classes = {
            'linear': GraphicRecord,
            'circular': CircularGraphicRecord,
            None: GraphicRecord
        }
        if record_class in classes:
            record_class = classes[record_class]

        if isinstance(record, str):
            record = SeqIO.read(record, "genbank")
        filtered_features = self.compute_filtered_features(record.features)
        return record_class(
            sequence_length=len(record),
            sequence=str(record.seq),
            features=[
                self.translate_feature(feature)
                for feature in filtered_features
                if feature.location is not None
            ], **self.graphic_record_parameters
        )
