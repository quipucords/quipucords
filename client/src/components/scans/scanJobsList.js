import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { Dropdown, EmptyState, Grid, Icon, MenuItem, Pager } from 'patternfly-react';
import _ from 'lodash';
import * as moment from 'moment/moment';
import { connect, reduxActions } from '../../redux';
import { helpers } from '../../common/helpers';
import { dictionary } from '../../constants/dictionaryConstants';

class ScanJobsList extends React.Component {
  constructor() {
    super();

    this.state = {
      scanJobs: [],
      scanJobsError: false,
      scanJobsPending: false,
      page: 1,
      disableNext: true,
      disablePrevious: true
    };
  }

  componentDidMount() {
    this.refresh();
  }

  componentWillReceiveProps(nextProps) {
    const { lastRefresh } = this.props;
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, lastRefresh)) {
      this.refresh();
    }
  }

  onNextPage = () => {
    const { page } = this.state;

    this.setState({ page: page + 1 });
    this.refresh(page + 1);
  };

  onPreviousPage = () => {
    const { page } = this.state;

    this.setState({ page: page - 1 });
    this.refresh(page - 1);
  };

  refresh(passedPage) {
    const { scan, getScanJobs } = this.props;
    const { page } = this.state;

    this.setState({
      scanJobsPending: true,
      disableNext: true,
      disablePrevious: true
    });

    const queryObject = {
      page: passedPage === undefined ? page : passedPage,
      page_size: 100,
      ordering: 'name'
    };

    if (_.get(scan, 'id')) {
      getScanJobs(scan.id, queryObject)
        .then(results => {
          this.setState({
            scanJobsPending: false,
            scanJobs: _.get(results.value, 'data.results')
          });
        })
        .catch(error => {
          this.setState({
            scanJobsPending: false,
            scanJobsError: helpers.getMessageFromResults(error).message
          });
        });
    }
  }

  renderJob(job) {
    const { scan, onSummaryDownload, onDetailedDownload } = this.props;

    if (job.id === _.get(scan, 'most_recent.id')) {
      return null;
    }

    const scanDescription = dictionary[job.status] || '';
    const statusIconInfo = helpers.scanStatusIcon(job.status);
    const classes = cx('scan-job-status-icon', ...statusIconInfo.classNames);
    const icon = <Icon className={classes} type={statusIconInfo.type} name={statusIconInfo.name} />;

    let scanTime = _.get(job, 'end_time');

    if (job.status === 'pending' || job.status === 'running') {
      scanTime = _.get(job, 'start_time');
    }

    return (
      <Grid.Row key={job.id}>
        <Grid.Col xs={6} sm={3}>
          {icon}
          {scanDescription}
        </Grid.Col>
        <Grid.Col xs={3} sm={2} smPush={3}>
          <Icon className="scan-job-status-icon systems" type="pf" name="ok" />
          {job.systems_scanned > 0 ? job.systems_scanned : '0'}
        </Grid.Col>
        <Grid.Col xs={3} sm={2} smPush={5}>
          {job.report_id > 0 && (
            <Dropdown id={helpers.generateId()} className="pull-right" pullRight>
              <Dropdown.Toggle useAnchor>
                <Icon type="fa" name="download" />
              </Dropdown.Toggle>
              <Dropdown.Menu>
                <MenuItem eventKey="1" onClick={() => onSummaryDownload(job.report_id)}>
                  Summary Report
                </MenuItem>
                <MenuItem eventKey="2" onClick={() => onDetailedDownload(job.report_id)}>
                  Detailed Report
                </MenuItem>
              </Dropdown.Menu>
            </Dropdown>
          )}
        </Grid.Col>
        <Grid.Col xs={6} sm={3} smPull={4}>
          {moment
            .utc(scanTime)
            .utcOffset(moment().utcOffset())
            .fromNow()}
        </Grid.Col>
        <Grid.Col xs={3} sm={2} smPull={2}>
          <Icon className="scan-job-status-icon systems" type="pf" name="error-circle-o" />
          {job.systems_failed > 0 ? job.systems_failed : '0'}
        </Grid.Col>
      </Grid.Row>
    );
  }

  render() {
    const { scan } = this.props;
    const { scanJobs, scanJobsPending, scanJobsError, disableNext, disablePrevious } = this.state;

    if (scanJobsPending === true) {
      return (
        <EmptyState>
          <EmptyState.Icon name="spinner spinner-xl" />
          <EmptyState.Title>Loading scan jobs...</EmptyState.Title>
        </EmptyState>
      );
    }

    if (scanJobsError) {
      return (
        <EmptyState>
          <EmptyState.Icon name="error-circle-o" />
          <EmptyState.Title>Error retrieving scan jobs</EmptyState.Title>
          <EmptyState.Info>{scan.scanJobsError}</EmptyState.Info>
        </EmptyState>
      );
    }

    return (
      <React.Fragment>
        {(!disableNext || !disablePrevious) && (
          <Grid fluid>
            <Grid.Row>
              <Pager
                className="pager-sm"
                onNextPage={this.onNextPage}
                onPreviousPage={this.onPreviousPage}
                disableNext={disableNext}
                disablePrevious={disablePrevious}
              />
            </Grid.Row>
          </Grid>
        )}
        <Grid fluid className="host-list">
          {scanJobs && scanJobs.map(job => this.renderJob(job))}
        </Grid>
      </React.Fragment>
    );
  }
}

ScanJobsList.propTypes = {
  scan: PropTypes.object,
  lastRefresh: PropTypes.number,
  onSummaryDownload: PropTypes.func,
  onDetailedDownload: PropTypes.func,
  getScanJobs: PropTypes.func
};

ScanJobsList.defaultProps = {
  scan: {},
  lastRefresh: 0,
  onSummaryDownload: helpers.noop,
  onDetailedDownload: helpers.noop,
  getScanJobs: helpers.noop
};

const mapDispatchToProps = dispatch => ({
  getScanJobs: (id, query) => dispatch(reduxActions.scans.getScanJobs(id, query))
});

const mapStateToProps = () => ({});

const ConnectedScanJobsList = connect(
  mapStateToProps,
  mapDispatchToProps
)(ScanJobsList);

export { ConnectedScanJobsList as default, ConnectedScanJobsList, ScanJobsList };
