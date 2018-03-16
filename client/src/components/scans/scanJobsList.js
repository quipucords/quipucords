import React from 'react';
import PropTypes from 'prop-types';
import cx from 'classnames';
import { Dropdown, EmptyState, Grid, Icon, MenuItem, Modal } from 'patternfly-react';
import _ from 'lodash';
import * as moment from 'moment/moment';
import helpers from '../../common/helpers';

const ScanJobsList = ({ scan, scanJobs, scanJobsPending, scanJobsError, onSummaryDownload, onDetailedDownload }) => {
  const renderJob = job => {
    const scanDescription = helpers.scanStatusString(job.status);
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
