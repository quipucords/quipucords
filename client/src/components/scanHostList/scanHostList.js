import _ from 'lodash';
import React from 'react';
import ReactDOM from 'react-dom';
import PropTypes from 'prop-types';

import helpers from '../../common/helpers';
import { connect } from 'react-redux';
import { Button, EmptyState, Grid } from 'patternfly-react';
import { getConnectionScanResults, getInspectionScanResults } from '../../redux/actions/scansActions';

class ScanHostList extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['onNextPage', 'onPreviousPage']);

    this.state = {
      scanResults: [],
      scanResultsError: false,
      connectionScanResultsPending: false,
      inspectionScanResultsPending: false,
      page: 1,
      moreResults: false,
      nextSetSize: 0,
      prevResults: []
    };
  }

  componentDidMount() {
    this.refresh(this.props);
  }

  componentWillReceiveProps(nextProps) {
    // Check for changes resulting in a fetch
    if (
      !_.isEqual(nextProps.lastRefresh, this.props.lastRefresh) ||
      nextProps.status !== this.props.status ||
      nextProps.useConnectionResults !== this.props.useConnectionResults ||
      nextProps.useInspectionResults !== this.props.useInspectionResults
    ) {
      this.refresh(nextProps);
    }
  }

  componentDidUpdate() {
    if (this.scrollToHost) {
      this.scrollHostListToHost(this.scrollToHost);
      this.scrollToHost = null;
    }
  }

  onNextPage() {
    this.setState({ page: this.state.page + 1 });
    this.refresh(this.props, this.state.page + 1);
  }

  onPreviousPage() {
    this.setState({ page: this.state.page - 1 });
    this.refresh(this.props, this.state.page - 1);
  }

  addResults(results) {
    const { scanResults } = this.state;
    const { useConnectionResults, useInspectionResults } = this.props;
    const usePaging = !useConnectionResults || !useInspectionResults;

    const newResults = _.get(results, 'value.data.results', []);
    let allResults = [...scanResults, ...newResults];

    if (!usePaging) {
      allResults.sort((item1, item2) => {
        if (helpers.isIpAddress(item1.name) && helpers.isIpAddress(item2.name)) {
          const value1 = helpers.ipAddressValue(item1.name);
          const value2 = helpers.ipAddressValue(item2.name);

          return value1 - value2;
        }

        return item1.name.localeCompare(item2.name);
      });
    } else {
      this.scrollToHost = _.head(newResults);
    }

    return allResults;
  }

  getInspectionResults(page, status) {
    const { scanId, sourceId, getInspectionScanResults, useConnectionResults, useInspectionResults } = this.props;
    const usePaging = !useConnectionResults || !useInspectionResults;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status: status
    };

    if (sourceId) {
      queryObject.source_id = sourceId;
    }

    getInspectionScanResults(scanId, queryObject)
      .then(results => {
        const morePages = !usePaging && _.get(results.value, 'data.next') !== null;

        this.setState({
          inspectionScanResultsPending: morePages,
          scanResults: this.addResults(results),
          prevResults: morePages || this.state.connectionScanResultsPending ? this.state.prevResults : [],
          disableNext: !usePaging || _.get(results.value, 'data.next') === null,
          disablePrevious: !usePaging || _.get(results.value, 'data.previous') === null
        });

        if (morePages) {
          this.getInspectionResults(page + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          inspectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error),
          disableNext: true,
          disablePrevious: true
        });
      });
  }

  getConnectionResults(page, status) {
    const { scanId, sourceId, getConnectionScanResults, useConnectionResults, useInspectionResults } = this.props;
    const usePaging = !useConnectionResults || !useInspectionResults;

    const queryObject = {
      page: page === undefined ? this.state.page : page,
      page_size: 100,
      ordering: 'name',
      status: status
    };

    if (sourceId) {
      queryObject.source_id = sourceId;
    }

    getConnectionScanResults(scanId, queryObject)
      .then(results => {
        const allResults = this.addResults(results);
        const morePages = _.get(results.value, 'data.next') !== null;
        const fullCount = _.get(results.value, 'data.count');
        const nextSetSize = Math.min(fullCount - _.size(allResults), 100);

        this.setState({
          moreResults: morePages,
          nextSetSize: nextSetSize,
          connectionScanResultsPending: morePages && !usePaging,
          scanResults: allResults,
          prevResults: morePages || this.state.inspectionScanResultsPending ? this.state.prevResults : []
        });

        if (morePages && !usePaging) {
          this.getConnectionResults(page + 1, status);
        }
      })
      .catch(error => {
        this.setState({
          connectionScanResultsPending: false,
          scanResultsError: helpers.getErrorMessageFromResults(error),
          disableNext: true,
          disablePrevious: true
        });
      });
  }

  refresh(useProps, page = 1) {
    let { useConnectionResults, useInspectionResults, status } = useProps;

    this.setState({
      scanResultsPending: true,
      connectionScanResultsPending: useConnectionResults,
      inspectionScanResultsPending: useInspectionResults,
      scanResults: page === 1 ? [] : this.state.scanResults,
      prevResults: this.state.scanResults
    });

    if (useConnectionResults) {
      this.getConnectionResults(page, status);
    }

    if (useInspectionResults) {
      this.getInspectionResults(page, status);
    }
  }

  scrollHostListToHost(host) {
    const { scanResults } = this.state;
    const hostList = ReactDOM.findDOMNode(this.refs.hostList);
    const firstHost = ReactDOM.findDOMNode(_.get(this.refs, `host_${_.get(_.head(scanResults), 'name')}`));
    const scrollHost = ReactDOM.findDOMNode(_.get(this.refs, `host_${host.name}`));

    if (hostList && scrollHost) {
      hostList.scrollTop = hostList.scrollTop - _.get(firstHost, 'offsetTop') + scrollHost.offsetTop;
    }
  }

  renderResults(results) {
    const { renderHostRow } = this.props;
    const { moreResults, nextSetSize } = this.state;

    return (
      <div className="host-results">
        <Grid fluid className="host-list" ref="hostList">
          {results &&
            results.map((host, index) => (
              <Grid.Row key={index} ref={`host_${host.name}`}>
                {renderHostRow(host)}
              </Grid.Row>
            ))}
          {moreResults && (
            <Grid fluid>
              <Grid.Row>
                <Button bsStyle="link" className="show-next-button" onClick={this.onNextPage}>
                  Show next {nextSetSize} results
                </Button>
              </Grid.Row>
            </Grid>
          )}
        </Grid>
      </div>
    );
  }

  render() {
    const { status } = this.props;
    const {
      scanResults,
      connectionScanResultsPending,
      inspectionScanResultsPending,
      scanResultsError,
      prevResults
    } = this.state;

    if (inspectionScanResultsPending || connectionScanResultsPending) {
      return (
        <React.Fragment>
          <EmptyState>
            <EmptyState.Icon name="spinner spinner-xl" />
            <EmptyState.Title>Loading scan results...</EmptyState.Title>
          </EmptyState>
          <div className="hidden-results">{this.renderResults(prevResults)}</div>
        </React.Fragment>
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

    if (_.size(scanResults) === 0) {
      return (
        <EmptyState>
          <EmptyState.Icon name="warning-triangle-o" />
          <EmptyState.Title>
            {`${helpers.scanStatusString(status)} systems were not available, please refresh.`}
          </EmptyState.Title>
        </EmptyState>
      );
    }

    return this.renderResults(scanResults);
  }
}

ScanHostList.propTypes = {
  scanId: PropTypes.number,
  sourceId: PropTypes.number,
  lastRefresh: PropTypes.number,
  status: PropTypes.string,
  renderHostRow: PropTypes.func,
  useConnectionResults: PropTypes.bool,
  useInspectionResults: PropTypes.bool,
  getConnectionScanResults: PropTypes.func,
  getInspectionScanResults: PropTypes.func
};

ScanHostList.defaultProps = {
  useConnectionResults: false,
  useInspectionResults: false
};

const mapStateToProps = function(state) {
  return {};
};

const mapDispatchToProps = (dispatch, ownProps) => ({
  getConnectionScanResults: (id, query) => dispatch(getConnectionScanResults(id, query)),
  getInspectionScanResults: (id, query) => dispatch(getInspectionScanResults(id, query))
});

export default connect(mapStateToProps, mapDispatchToProps)(ScanHostList);
