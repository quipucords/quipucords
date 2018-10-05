import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';
import { Grid, Icon } from 'patternfly-react';
import _ from 'lodash';
import { helpers } from '../../common/helpers';
import { getScanJob } from '../../redux/actions/scansActions';

class ScanSourceList extends React.Component {
  constructor() {
    super();

    this.state = {
      sources: [],
      scanJob: []
    };
  }

  componentDidMount() {
    this.sortSources(_.get(this.props, 'scan'));
    this.refresh();
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, this.props.lastRefresh)) {
      this.refresh();
    }

    if (nextProps.scan !== this.props.scan) {
      this.sortSources(_.get(nextProps, 'scan'));
    }
  }

  refresh() {
    const { scan, getScanJob } = this.props;
    const jobId = _.get(scan, 'most_recent.id');

    if (jobId) {
      getScanJob(jobId).then(results => {
        this.setState({ scanJob: _.get(results.value, 'data') });
      });
    }
  }

  sortSources(scan) {
    const sources = [..._.get(scan, 'sources', [])];

    sources.sort((item1, item2) => {
      let cmp = item1.source_type.localeCompare(item2.source_type);
      if (cmp === 0) {
        cmp = item1.name.localeCompare(item2.name);
      }
      return cmp;
    });

    this.setState({ sources });
  }

  getSourceStatus(source) {
    const { scanJob } = this.state;

    if (!source || !scanJob) {
      return null;
    }

    // Get the tasks for this source
    const connectTask = _.find(scanJob.tasks, { source: source.id, scan_type: 'connect' });
    const inspectTask = _.find(scanJob.tasks, { source: source.id, scan_type: 'inspect' });

    if (_.get(connectTask, 'status') !== 'completed' || !inspectTask) {
      return `Connection Scan: ${_.get(connectTask, 'status_message', 'checking status...')}`;
    }

    return `Inspection Scan: ${_.get(inspectTask, 'status_message', 'checking status...')}`;
  }

  static renderSourceIcon(source) {
    const iconInfo = helpers.sourceTypeIcon(source.source_type);

    return <Icon type={iconInfo.type} name={iconInfo.name} />;
  }

  render() {
    const { sources } = this.state;

    return (
      <Grid fluid>
        {sources.map((item, index) => (
          <Grid.Row key={index}>
            <Grid.Col xs={4} md={3}>
              {ScanSourceList.renderSourceIcon(item)}
              &nbsp; {item.name}
            </Grid.Col>
            <Grid.Col xs={8} md={9}>
              {this.getSourceStatus(item)}
            </Grid.Col>
          </Grid.Row>
        ))}
      </Grid>
    );
  }
}

ScanSourceList.propTypes = {
  scan: PropTypes.object.isRequired,
  lastRefresh: PropTypes.number,
  getScanJob: PropTypes.func
};

const mapDispatchToProps = dispatch => ({
  getScanJob: id => dispatch(getScanJob(id))
});

const mapStateToProps = () => ({});

const ConnectedScanSourceList = connect(
  mapStateToProps,
  mapDispatchToProps
)(ScanSourceList);

export { ConnectedScanSourceList as default, ConnectedScanSourceList, ScanSourceList };
