import _ from 'lodash';
import React from 'react';
import PropTypes from 'prop-types';

import { EmptyState, Grid, Icon, Pager } from 'patternfly-react';
import helpers from '../../common/helpers';
import { connect } from 'react-redux';
import { getInspectionScanResults } from '../../redux/actions/scansActions';

class ScanSuccessHostList extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['onNextPage', 'onPreviousPage']);

    this.state = {
      scanResults: [],
      scanResultsError: false,
      scanResultsPending: false,
      page: 1,
      disableNext: true,
      disablePrevious: true
    };
  }

  componentDidMount() {
    this.refresh();
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (!_.isEqual(nextProps.lastRefresh, this.props.lastRefresh)) {
      this.refresh();
    }
  }

  onNextPage() {
    this.setState({ page: this.state.page + 1 });
    this.refresh(this.state.page + 1);
  }

  onPreviousPage() {
    this.setState({ page: this.state.page - 1 });
    this.refresh(this.state.page - 1);
  }

  refresh(page) {
    const { scan, getInspectionScanResults } = this.props;

    this.setState({
      scanResultsPending: true,
      disableNext: true,
      disablePrevious: true
    });

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status: 'success'
    };

    if (_.get(scan, 'most_recent.id')) {
      getInspectionScanResults(scan.most_recent.id, queryObject)
        .then(results => {
          this.setState({
            scanResultsPending: false,
            scanResults: _.get(results.value, 'data'),
            disableNext: _.get(results.value, 'data.next') === null,
            disablePrevious: _.get(results.value, 'data.previous') === null
          });
        })
        .catch(error => {
          this.setState({
            scanResultsPending: false,
            scanResultsError: helpers.getErrorMessageFromResults(error),
            disableNext: true,
            disablePrevious: true
          });
        });
    }
  }

  render() {
    const { scanResults, scanResultsPending, scanResultsError, disableNext, disablePrevious } = this.state;
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
      if (result.status === 'success') {
        displayHosts.push(result);
      }
    });

    if (_.size(displayHosts) === 0) {
      return (
        <EmptyState>
          <EmptyState.Icon name="warning-triangle-o" />
          <EmptyState.Title>
            {`${helpers.scanStatusString('success')} systems were not available, please refresh.`}
          </EmptyState.Title>
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
          {displayHosts &&
            displayHosts.map((host, index) => (
              <Grid.Row key={index}>
                <Grid.Col xs={6} sm={4}>
                  <span>
                    <Icon type="pf" name="ok" />
                    &nbsp; {host.name}
                  </span>
                </Grid.Col>
              </Grid.Row>
            ))}
        </Grid>
      </React.Fragment>
    );
  }
}

ScanSuccessHostList.propTypes = {
  scan: PropTypes.object,
  lastRefresh: PropTypes.number,
  getInspectionScanResults: PropTypes.func
};

const mapStateToProps = function(state) {
  return {};
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getInspectionScanResults: (id, query) => dispatch(getInspectionScanResults(id, query))
});

export default connect(mapStateToProps, mapDispatchToProps)(ScanSuccessHostList);
