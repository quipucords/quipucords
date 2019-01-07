import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Icon } from 'patternfly-react';
import _ from 'lodash';
import { connect, reduxActions } from '../../redux';
import { helpers } from '../../common/helpers';

class ScanSourceList extends React.Component {
  static renderSourceIcon(source) {
    const iconInfo = helpers.sourceTypeIcon(source.source_type);

    return <Icon type={iconInfo.type} name={iconInfo.name} />;
  }

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
    const { lastRefresh, scan } = this.props;
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, lastRefresh)) {
      this.refresh();
    }

    if (nextProps.scan !== scan) {
      this.sortSources(_.get(nextProps, 'scan'));
    }
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

  render() {
    const { sources } = this.state;

    return (
      <Grid fluid>
        {sources.map(item => (
          <Grid.Row key={item.id}>
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

ScanSourceList.defaultProps = {
  lastRefresh: 0,
  getScanJob: helpers.noop
};

const mapDispatchToProps = dispatch => ({
  getScanJob: id => dispatch(reduxActions.scans.getScanJob(id))
});

const mapStateToProps = () => ({});

const ConnectedScanSourceList = connect(
  mapStateToProps,
  mapDispatchToProps
)(ScanSourceList);

export { ConnectedScanSourceList as default, ConnectedScanSourceList, ScanSourceList };
