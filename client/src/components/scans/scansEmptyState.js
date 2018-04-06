import React from 'react';
import PropTypes from 'prop-types';
import { Button, EmptyState, Grid, Row } from 'patternfly-react';
import SourcesEmptyState from '../sources/sourcesEmptyState';

const ScansEmptyState = ({ onAddSource, sourcesExist }) => {
  if (sourcesExist) {
    return (
      <Grid fluid>
        <Row>
          <EmptyState className="full-page-blank-slate">
            <EmptyState.Icon />
            <EmptyState.Title>No scans exist yet</EmptyState.Title>
            <EmptyState.Info>Select a Source to scan from the Sources page.</EmptyState.Info>
            <EmptyState.Action>
              <Button bsStyle="primary" bsSize="large" onClick={onAddSource}>
                Go to Sources
              </Button>
            </EmptyState.Action>
          </EmptyState>
        </Row>
      </Grid>
    );
  }

  return <SourcesEmptyState onAddSource={onAddSource} />;
};

ScansEmptyState.propTypes = {
  onAddSource: PropTypes.func,
  sourcesExist: PropTypes.bool
};

export default ScansEmptyState;
