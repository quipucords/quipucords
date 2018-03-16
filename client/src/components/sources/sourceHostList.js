import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import { EmptyState, Grid, Icon } from 'patternfly-react';
import helpers from '../../common/helpers';

const SourceHostList = ({ source, scanResults, scanResultsError, scanResultsPending, status }) => {
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

  let results = _.get(scanResults, 'results', []);
  let displayHosts = [];
  _.forEach(results, result => {
    if (result.status === status && _.get(result, 'source.id') === source.id) {
      displayHosts.push(result);
    }
  });

  if (_.size(displayHosts) === 0) {
    return (
      <EmptyState>
        <EmptyState.Icon name="warning-triangle-o" />
        <EmptyState.Title>
          {`${helpers.scanStatusString(status)} authentications were not available, please refresh.`}
        </EmptyState.Title>
      </EmptyState>
    );
  }

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

SourceHostList.propTypes = {
  source: PropTypes.object,
  scanResults: PropTypes.object,
  scanResultsError: PropTypes.string,
  scanResultsPending: PropTypes.bool,
  status: PropTypes.string
};

export default SourceHostList;
