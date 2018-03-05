import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import { Dropdown, EmptyState, Grid, Icon, MenuItem, Modal } from 'patternfly-react';
import * as moment from 'moment/moment';
import helpers from '../../common/helpers';

class ScanJobsList extends React.Component {
  renderJob(job) {
    const { onSummaryDownload, onDetailedDownload } = this.props;
    let scanDescription = '';

    let icon = null;
    let scanTime = _.get(job, 'end_time');

    switch (job.status) {
      case 'completed':
        scanDescription = 'Complete';
        icon = <Icon className="scan-job-status-icon" type="pf" name="ok" />;
        break;
      case 'failed':
        scanDescription = 'Failed';
        icon = <Icon className="scan-job-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'canceled':
        scanDescription = 'Canceled';
        icon = <Icon className="scan-job-status-icon" type="pf" name="error-circle-o" />;
        break;
      case 'created':
        scanDescription = 'Created';
        icon = <Icon className="scan-job-status-icon invisible" type="fa" name="spinner" />;
        break;
      case 'pending':
        scanDescription = 'Pending';
        icon = <Icon className="scan-job-status-icon invisible" type="fa" name="spinner" />;
        scanTime = _.get(job, 'start_time');
        break;
      case 'running':
        scanDescription = 'In Progress';
        icon = <Icon className="scan-job-status-icon fa-spin" type="fa" name="spinner" />;
        scanTime = _.get(job, 'start_time');
        break;
      case 'paused':
        scanDescription = 'Paused';
        icon = <Icon className="scan-job-status-icon" type="pf" name="warning-triangle-o" />;
        break;
      default:
        return null;
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
          {job.status === 'completed' && (
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

    if (scan.scanJobsPending === true) {
      return (
        <Modal bsSize="lg" backdrop={false} show animation={false}>
          <Modal.Body>
            <div className="spinner spinner-xl" />
            <div className="text-center">Loading scan jobs...</div>
          </Modal.Body>
        </Modal>
      );
    }

    if (scan.scanJobsError) {
      return (
        <EmptyState>
          <EmptyState.Icon name="error-circle-o" />
          <EmptyState.Title>Error retrieving scan jobs</EmptyState.Title>
          <EmptyState.info>{scan.scanJobsError}</EmptyState.info>
        </EmptyState>
      );
    }

    return (
      <Grid fluid>
        {_.get(scan, 'scanJobs', []).map(job => {
          return job.id !== _.get(scan, 'most_recent.id') ? this.renderJob(job) : null;
        })}
      </Grid>
    );
  }
}

ScanJobsList.propTypes = {
  scan: PropTypes.object,
  onSummaryDownload: PropTypes.func,
  onDetailedDownload: PropTypes.func
};

export default ScanJobsList;
