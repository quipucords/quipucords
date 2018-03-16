import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import { EmptyState, Grid, Icon } from 'patternfly-react';

const ScansHostList = ({ status, scanResults, scanResultsPending, scanResultsError }) => {
  if (scanResultsPending === true) {
    return (
      <EmptyState>
        <EmptyState.Icon name="spinner spinner-xl" />
        <EmptyState.Title>Loading scan results...</EmptyState.Title>
      </EmptyState>
    );
  }

  if (scanResultsError) {
    return (
      <EmptyState>
        <EmptyState.Icon name="error-circle-o" />
        <EmptyState.Title>Error retrieving scan results</EmptyState.Title>
        <EmptyState.Info>{scanResultsError}</EmptyState.Info>
      </EmptyState>
    );
  }

  let connectionResults = _.get(scanResults, 'connection_results', []);

  let displayHosts = [];
  _.forEach(connectionResults.task_results, taskResult => {
    _.forEach(taskResult.systems, system => {
      if (system.status === status) {
        displayHosts.push(system);
      }
    });
  });

  displayHosts.sort((item1, item2) => {
    return item1.name.localeCompare(item2.name);
  });

  return (
    <Grid fluid>
      {displayHosts &&
        displayHosts.map((host, index) => (
          <Grid.Row key={index}>
            <Grid.Col xs={6} sm={4}>
              <span>
                <Icon type="pf" name={host.status === 'success' ? 'ok' : 'error-circle-o'} />
                &nbsp; {host.name}
              </span>
            </Grid.Col>
            {host.status === 'success' && (
              <Grid.Col xs={6} sm={4}>
                <span>
                  <Icon type="fa" name="id-card" />
                  &nbsp; {host.credential.name}
                </span>
              </Grid.Col>
            )}
          </Grid.Row>
        ))}
    </Grid>
  );
};

ScansHostList.propTypes = {
  scanResults: PropTypes.object,
  scanResultsError: PropTypes.string,
  scanResultsPending: PropTypes.bool,
  status: PropTypes.string
};

export default ScansHostList;
