import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import { Dropdown, EmptyState, Grid, Icon, MenuItem, Modal } from 'patternfly-react';
import * as moment from 'moment/moment';
import helpers from '../../common/helpers';

const ScanJobsList = ({ scan, scanJobs, scanJobsPending, scanJobsError, onSummaryDownload, onDetailedDownload }) => {
  const renderJob = job => {
    let scanDescription = helpers.scanStatusString(job.status);

    let scanTime = _.get(job, 'end_time');
    let statusIconInfo = helpers.scanStatusIcon(job.status);
    let icon = <Icon className="scan-job-status-icon" type={statusIconInfo.type} name={statusIconInfo.name} />;

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
  };

  if (scanJobsPending === true) {
    return (
      <Modal bsSize="lg" backdrop={false} show animation={false}>
        <Modal.Body>
          <div className="spinner spinner-xl" />
          <div className="text-center">Loading scan jobs...</div>
        </Modal.Body>
      </Modal>
    );
  }

  if (scanJobsError) {
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
      {scanJobs &&
        scanJobs.map(job => {
          return job.id !== _.get(scan, 'most_recent.id') ? renderJob(job) : null;
        })}
    </Grid>
  );
};

ScanJobsList.propTypes = {
  scan: PropTypes.object,
  scanJobs: PropTypes.array,
  scanJobsError: PropTypes.string,
  scanJobsPending: PropTypes.bool,
  onSummaryDownload: PropTypes.func,
  onDetailedDownload: PropTypes.func
};

export default ScanJobsList;
